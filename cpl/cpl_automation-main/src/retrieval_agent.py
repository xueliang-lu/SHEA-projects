"""
CPL Automation System
Author: Sunil Paudel

Notes:
- Mandatory step: run AI retrieval first. All external units must be enriched via Playwright before matching.
"""

from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from html import unescape
from typing import Dict, List, Optional
from urllib.parse import parse_qs, quote_plus, urljoin, urlparse

import requests
from requests import RequestException

from .llm_assist import rank_urls_for_unit, structure_unit_content


USER_AGENT = "Mozilla/5.0 (compatible; CPLBot/0.1; +https://shea.example)"
SHEA_BIT_URL = "https://shea.edu.au/courses/bachelor-of-information-technology/"
SHEA_MIT_URL = "https://shea.edu.au/courses/master-of-information-technology/"


def _is_unit_like_url(url: str) -> bool:
    """Allow likely unit handbook pages and reject generic search/navigation pages."""
    u = (url or "").lower()
    if not u.startswith("http"):
        return False

    reject_tokens = [
        "/search",
        "?q=",
        "?s=",
        "/news",
        "/events",
        "/about",
        "/contact",
        "/study-at",
    ]
    if any(tok in u for tok in reject_tokens):
        return False

    allow_tokens = [
        "/units/",
        "/unit/",
        "/subjects/",
        "/subject/",
        "/handbook/",
        "/course-handbook/",
        "unit",
    ]
    return any(tok in u for tok in allow_tokens)


@dataclass
class RetrievalResult:
    success: bool
    source_url: str
    retrieval_mode: str
    retrieval_confidence: float
    description: str
    learning_outcomes: str
    topics: str
    credit_points: str
    aqf_level: str
    error: Optional[str] = None
    debug_steps: Optional[List[str]] = None


def _strip_html(html: str) -> str:
    # Remove script/style blocks first, then tags.
    text = re.sub(r"(?is)<script\b.*?</script>", " ", html)
    text = re.sub(r"(?is)<style\b.*?</style>", " ", text)
    text = re.sub(r"(?is)@media[^\{]*\{[^\}]*\}", " ", text)
    text = re.sub(r"(?is)\.[a-z0-9_\-]+\s*\{[^\}]*\}", " ", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = unescape(text)
    text = re.sub(r"\b(svg-inline--fa|fa-w-\d+|vu-page-courses|vu-page-units)\b", " ", text, flags=re.I)
    return re.sub(r"\s+", " ", text).strip()


def resolve_candidate_urls(
    unit_code: str,
    title: str,
    institution: str = "",
    university_url: str = "",
    request_timeout_seconds: int = 10,
) -> List[str]:
    urls: List[str] = []

    if university_url:
        base = university_url.rstrip("/")
        parsed = urlparse(base)
        site_root = f"{parsed.scheme}://{parsed.netloc}" if parsed.scheme and parsed.netloc else base
        # Direct unit-page candidates first (works even when search engines are blocked).
        urls.extend(
            [
                f"{site_root}/units/{unit_code}",
                f"{site_root}/unit/{unit_code}",
                f"{site_root}/subjects/{unit_code}",
                f"{site_root}/subject/{unit_code}",
                f"{site_root}/search?query={quote_plus(unit_code)}",
                f"{base}/?s={quote_plus(unit_code)}",
            ]
        )

    query = f"{institution} {unit_code} {title} unit outline handbook"
    if university_url:
        domain = urlparse(university_url).netloc
        if domain:
            query = f"site:{domain} {unit_code} {title} unit"

    url = f"https://duckduckgo.com/html/?q={quote_plus(query)}"
    try:
        r = requests.get(url, timeout=request_timeout_seconds, headers={"User-Agent": USER_AGENT})
        r.raise_for_status()
    except RequestException:
        # If search is blocked, still return seeded URLs from university_url.
        return list(dict.fromkeys([u for u in urls if u]))

    for match in re.finditer(r'href="([^"]+)"', r.text):
        href = match.group(1)
        if "duckduckgo.com/l/?" in href:
            qs = parse_qs(urlparse(href).query)
            target = qs.get("uddg", [""])[0]
            if target.startswith("http"):
                urls.append(target)
        elif href.startswith("http"):
            urls.append(href)

    # keep first unique likely unit-level links (not generic search pages)
    dedup: List[str] = []
    for u in urls:
        if u not in dedup and _is_unit_like_url(u):
            dedup.append(u)
        if len(dedup) >= 5:
            break
    return dedup


def _looks_like_correct_unit_page(text: str, unit_code: str) -> bool:
    if not unit_code:
        return False
    tl = (text or "").lower()
    code = unit_code.lower()
    # Must mention the requested unit code and at least one unit-like cue.
    return (code in tl) and any(cue in tl for cue in ["learning outcomes", "assessment", "unit", "subject", "credit"])


def _extract_sections(text: str) -> Dict[str, str]:
    text_l = text.lower()

    def _slice_between(start_pat: str, end_pats: List[str], limit: int = 1800) -> str:
        m = re.search(start_pat, text, flags=re.I)
        if not m:
            return ""
        start = m.end()
        end = len(text)
        tail = text[start:]
        for ep in end_pats:
            em = re.search(ep, tail, flags=re.I)
            if em:
                end = min(end, start + em.start())
        out = " ".join(text[start:end].split())
        return out[:limit]

    # Prefer unit-page sections, not whole-page boilerplate.
    desc = _slice_between(
        r"\boverview\b",
        [r"\blearning outcomes?\b", r"\bassessment\b", r"\bas part of a course\b", r"\benquire\b"],
        limit=1800,
    )
    if not desc:
        desc = _slice_between(
            r"\bintroduction\b",
            [r"\blearning outcomes?\b", r"\bassessment\b", r"\bprerequisites?\b"],
            limit=1800,
        )
    if not desc:
        desc = text[:1800]

    outcomes = _slice_between(
        r"\blearning outcomes?\b",
        [r"\bassessment\b", r"\bstudy as a single unit\b", r"\bas part of a course\b", r"\benquire\b"],
        limit=1200,
    )
    if not outcomes:
        m = re.search(r"(learning outcomes?|outcomes?)[:\-\s]+(.{0,1500})", text, flags=re.I)
        if m:
            outcomes = m.group(2)

    topics = _slice_between(
        r"\b(topics?|content)\b",
        [r"\blearning outcomes?\b", r"\bassessment\b", r"\benquire\b"],
        limit=1000,
    )
    if not topics:
        m2 = re.search(r"(topics?|content)[:\-\s]+(.{0,1000})", text, flags=re.I)
        if m2:
            topics = m2.group(2)

    cp = ""
    m3 = re.search(r"(\b\d{1,2}\s*(credit points?|cp)\b)", text_l)
    if m3:
        cp = m3.group(1)

    aqf = ""
    m4 = re.search(r"aqf\s*level\s*(\d{1,2})", text_l)
    if m4:
        aqf = m4.group(1)

    return {
        "description": " ".join(desc.split())[:1800],
        "learning_outcomes": " ".join(outcomes.split())[:1200],
        "topics": " ".join(topics.split())[:1000],
        "credit_points": cp,
        "aqf_level": aqf,
    }


def _score_quality(fields: Dict[str, str]) -> float:
    score = 0.0
    if len(fields.get("description", "")) > 500:
        score += 0.45
    if len(fields.get("learning_outcomes", "")) > 120:
        score += 0.3
    if len(fields.get("topics", "")) > 80:
        score += 0.15
    if fields.get("credit_points"):
        score += 0.05
    if fields.get("aqf_level"):
        score += 0.05
    return min(score, 1.0)


def _retrieve_static(url: str, request_timeout_seconds: int = 10) -> RetrievalResult:
    try:
        r = requests.get(url, timeout=request_timeout_seconds, headers={"User-Agent": USER_AGENT})
        r.raise_for_status()
    except RequestException as exc:
        return RetrievalResult(False, url, "static", 0.0, "", "", "", "", "", f"Static fetch error: {exc}")

    text = _strip_html(r.text)
    fields = _extract_sections(text)
    llm_fields = structure_unit_content(text)
    if llm_fields:
        for k, v in llm_fields.items():
            if v and len(str(v).strip()) > len(str(fields.get(k, "")).strip()):
                fields[k] = str(v)
    conf = _score_quality(fields)
    return RetrievalResult(
        success=conf >= 0.35,
        source_url=url,
        retrieval_mode="static",
        retrieval_confidence=conf,
        **fields,
        error=None if conf >= 0.35 else "Insufficient content from static fetch",
    )


def _retrieve_playwright(url: str, request_timeout_seconds: int = 10) -> RetrievalResult:
    try:
        from playwright.sync_api import sync_playwright
    except Exception as exc:
        return RetrievalResult(False, url, "playwright_dom", 0.0, "", "", "", "", "", f"Playwright unavailable: {exc}")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, wait_until="networkidle", timeout=request_timeout_seconds * 1000)
            # user-like actions
            for _ in range(3):
                page.mouse.wheel(0, 1800)
            for label in ["Learning outcomes", "Outcomes", "Unit details", "Outline", "Description"]:
                try:
                    page.get_by_text(label, exact=False).first.click(timeout=1000)
                except Exception:
                    pass

            html = page.content()
            browser.close()

        text = _strip_html(html)
        fields = _extract_sections(text)
        llm_fields = structure_unit_content(text)
        if llm_fields:
            for k, v in llm_fields.items():
                if v and len(str(v).strip()) > len(str(fields.get(k, "")).strip()):
                    fields[k] = str(v)
        conf = _score_quality(fields)
        return RetrievalResult(
            success=conf >= 0.4,
            source_url=url,
            retrieval_mode="playwright_dom",
            retrieval_confidence=conf,
            **fields,
            error=None if conf >= 0.4 else "Insufficient content from Playwright rendering",
        )
    except Exception as exc:
        return RetrievalResult(False, url, "playwright_dom", 0.0, "", "", "", "", "", str(exc))


def _fetch_html_as_user(url: str, request_timeout_seconds: int = 10) -> str:
    """Fetch page as a user (Playwright first, requests fallback)."""
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, wait_until="networkidle", timeout=request_timeout_seconds * 1000)
            page.mouse.wheel(0, 1200)
            page.wait_for_timeout(400)
            html = page.content()
            browser.close()
            return html
    except Exception:
        try:
            r = requests.get(url, timeout=request_timeout_seconds, headers={"User-Agent": USER_AGENT})
            r.raise_for_status()
            return r.text
        except Exception:
            return ""


def _discover_unit_link_from_course_page(course_url: str, unit_code: str, request_timeout_seconds: int = 12) -> str:
    """Navigate course page like a user and try to find a specific unit link."""
    if not course_url or not unit_code:
        return ""
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(course_url, wait_until="domcontentloaded", timeout=request_timeout_seconds * 1000)
            page.wait_for_timeout(800)

            # User-like exploration of likely sections.
            for label in [
                "Course structure", "Units", "Unit", "Subjects", "What you will study", "Study plan", "Handbook"
            ]:
                try:
                    page.get_by_text(label, exact=False).first.click(timeout=900)
                    page.wait_for_timeout(500)
                except Exception:
                    pass

            for _ in range(3):
                page.mouse.wheel(0, 1800)
                page.wait_for_timeout(200)

            anchors = page.locator("a[href]")
            count = min(anchors.count(), 1200)
            candidate = ""
            for i in range(count):
                try:
                    href = anchors.nth(i).get_attribute("href") or ""
                    label = (anchors.nth(i).inner_text(timeout=100) or "").strip()
                    full = urljoin(course_url, href)
                    blob = f"{full} {label}".upper()
                    if unit_code.upper() in blob and _is_unit_like_url(full):
                        candidate = full
                        break
                except Exception:
                    continue

            browser.close()
            return candidate
    except Exception:
        return ""


def _extract_unit_links(course_url: str, html: str) -> List[str]:
    links: List[str] = []
    for m in re.finditer(r"<a[^>]+href=[\"']([^\"']+)[\"'][^>]*>([\s\S]*?)</a>", html, flags=re.I):
        href = (m.group(1) or "").strip()
        label = _strip_html(m.group(2) or "")
        full = urljoin(course_url, href)
        candidate_blob = f"{full} {label}"
        if re.search(r"\b[A-Z]{2,6}\d{3,4}\b", candidate_blob) and full.startswith("http"):
            if full not in links:
                links.append(full)
    return links


def harvest_course_structure_units(
    course_url: str,
    request_timeout_seconds: int = 10,
    max_workers: int = 6,
) -> Dict[str, Dict[str, str]]:
    """Extract unit-level description/outcomes from a course page using parallel user-like visits."""
    out: Dict[str, Dict[str, str]] = {}
    if not (course_url or "").startswith("http"):
        return out

    html = _fetch_html_as_user(course_url, request_timeout_seconds=request_timeout_seconds)
    if not html:
        return out

    links = _extract_unit_links(course_url, html)

    def _scrape_unit(link: str) -> tuple[str, Dict[str, str]]:
        code_match = re.search(r"\b([A-Z]{2,6}\d{3,4})\b", link, flags=re.I)
        unit_code = code_match.group(1).upper() if code_match else ""
        if not unit_code:
            return "", {}

        page_html = _fetch_html_as_user(link, request_timeout_seconds=request_timeout_seconds)
        if not page_html:
            return "", {}

        text = _strip_html(page_html)
        if not _looks_like_correct_unit_page(text, unit_code):
            return "", {}
        fields = _extract_sections(text)

        title = ""
        tmatch = re.search(r"\b[A-Z]{2,6}\d{3,4}\b\s*[-–—:]?\s*([^|]{4,160})", text)
        if tmatch:
            title = tmatch.group(1).strip()

        payload = {
            "title": title,
            "description": fields.get("description", ""),
            "learning_outcomes": fields.get("learning_outcomes", ""),
            "topics": fields.get("topics", ""),
            "source_url": link,
        }
        if payload["description"] or payload["learning_outcomes"] or payload["topics"]:
            return unit_code, payload
        return "", {}

    with ThreadPoolExecutor(max_workers=max(1, min(max_workers, 12))) as ex:
        futures = [ex.submit(_scrape_unit, link) for link in links[:150]]
        for f in as_completed(futures):
            try:
                code, payload = f.result()
                if code and payload:
                    out[code] = payload
            except Exception:
                continue

    return out


def harvest_course_page_summary(course_url: str, request_timeout_seconds: int = 10) -> Dict[str, str]:
    """Capture key course-page sections for dashboard display."""
    html = _fetch_html_as_user(course_url, request_timeout_seconds=request_timeout_seconds)
    if not html:
        return {}

    text = _strip_html(html)

    def _slice(start_pat: str, end_pats: List[str], limit: int = 2200) -> str:
        m = re.search(start_pat, text, flags=re.I)
        if not m:
            return ""
        start = m.end()
        end = len(text)
        for ep in end_pats:
            em = re.search(ep, text[start:], flags=re.I)
            if em:
                end = min(end, start + em.start())
        return text[start:end].strip()[:limit]

    overview = _slice(r"\boverview\b", [r"\blearning outcomes\b", r"\bentry requirements\b", r"\bcourse structure\b", r"\bfees\b"])
    learning = _slice(r"\blearning outcomes\b", [r"\bentry requirements\b", r"\bcourse structure\b", r"\bfees\b", r"\bcareers\b"])
    structure = _slice(r"\bcourse structure\b", [r"\bunits\b", r"\bfees\b", r"\bcareers\b", r"\bstart dates\b"])
    careers = _slice(r"\bcareers\b", [r"\bstart dates\b", r"\bprofessional accreditation\b", r"\brelated courses\b"])

    return {
        "course_url": course_url,
        "page_title": text[:220],
        "overview": overview,
        "learning_outcomes": learning,
        "course_structure": structure,
        "careers": careers,
    }


def harvest_units_by_codes(
    base_course_url: str,
    unit_codes: List[str],
    request_timeout_seconds: int = 10,
    max_workers: int = 6,
) -> Dict[str, Dict[str, str]]:
    """Directly fetch unit pages by code (useful when course page does not expose all links)."""
    out: Dict[str, Dict[str, str]] = {}
    domain = urlparse(base_course_url).netloc
    if not domain:
        return out

    codes = sorted({(c or "").strip().upper() for c in unit_codes if (c or "").strip()})

    def _fetch_code(code: str) -> tuple[str, Dict[str, str]]:
        url = f"https://{domain}/units/{code}"
        html = _fetch_html_as_user(url, request_timeout_seconds=request_timeout_seconds)
        if not html:
            return "", {}
        text = _strip_html(html)
        if not _looks_like_correct_unit_page(text, code):
            return "", {}
        title = ""
        tmatch = re.search(rf"\b{re.escape(code)}\b\s*[-–—:]?\s*([^|]{{4,160}})", text, flags=re.I)
        if tmatch:
            title = tmatch.group(1).strip()
        fields = _extract_sections(text)
        payload = {
            "title": title,
            "description": fields.get("description", ""),
            "learning_outcomes": fields.get("learning_outcomes", ""),
            "topics": fields.get("topics", ""),
            "source_url": url,
        }
        if payload["description"] or payload["learning_outcomes"] or payload["topics"]:
            return code, payload
        return "", {}

    with ThreadPoolExecutor(max_workers=max(1, min(max_workers, 12))) as ex:
        futures = [ex.submit(_fetch_code, c) for c in codes]
        for f in as_completed(futures):
            try:
                code, payload = f.result()
                if code and payload:
                    out[code] = payload
            except Exception:
                continue

    return out


def harvest_shea_units_for_qualification(
    qualification: str,
    request_timeout_seconds: int = 10,
    max_workers: int = 6,
) -> Dict[str, Dict[str, str]]:
    q = (qualification or "").strip().lower()
    shea_url = SHEA_MIT_URL if q == "master" else SHEA_BIT_URL
    return harvest_course_structure_units(
        shea_url,
        request_timeout_seconds=request_timeout_seconds,
        max_workers=max_workers,
    )


def enrich_external_unit(
    unit_code: str,
    title: str,
    institution: str = "",
    university_url: str = "",
    request_timeout_seconds: int = 10,
) -> RetrievalResult:
    debug_steps: List[str] = [
        f"query: {institution} {unit_code} {title}",
        f"university_url: {university_url or '-'}",
        f"timeout_seconds: {request_timeout_seconds}",
    ]
    urls = resolve_candidate_urls(
        unit_code=unit_code,
        title=title,
        institution=institution,
        university_url=university_url,
        request_timeout_seconds=request_timeout_seconds,
    )

    # MCP-like behavior: first browse the given course URL and discover the right unit link.
    discovered = _discover_unit_link_from_course_page(
        course_url=university_url,
        unit_code=unit_code,
        request_timeout_seconds=request_timeout_seconds,
    ) if university_url else ""
    if discovered:
        urls = [discovered] + [u for u in urls if u != discovered]
        debug_steps.append(f"course_navigation_hit: {discovered}")

    urls = rank_urls_for_unit(unit_code=unit_code, title=title, institution=institution, urls=urls)
    debug_steps.append(f"candidate_urls: {len(urls)}")
    if not urls:
        return RetrievalResult(
            False,
            "",
            "none",
            0.0,
            "",
            "",
            "",
            "",
            "",
            "Insufficient evidence: no unit-level URLs found (search/home pages filtered)",
            debug_steps,
        )

    best: Optional[RetrievalResult] = None

    for i, url in enumerate(urls[:5], start=1):
        debug_steps.append(f"[{i}] playwright_try: {url}")

        # Mandatory user-like retrieval first.
        p = _retrieve_playwright(url, request_timeout_seconds=request_timeout_seconds)
        p.debug_steps = debug_steps + [f"[{i}] playwright_result: success={p.success} conf={p.retrieval_confidence:.2f} err={p.error or '-'}"]
        if p.retrieval_confidence > (best.retrieval_confidence if best else 0.0):
            best = p
        if p.success:
            return p

        debug_steps.append(f"[{i}] static_try: {url}")
        # Static fallback only when Playwright could not get enough content.
        s = _retrieve_static(url, request_timeout_seconds=request_timeout_seconds)
        s.debug_steps = debug_steps + [f"[{i}] static_result: success={s.success} conf={s.retrieval_confidence:.2f} err={s.error or '-'}"]
        if (best is None) or (s.retrieval_confidence > best.retrieval_confidence):
            best = s

    if best:
        best.debug_steps = (best.debug_steps or []) + ["final: best_available_result_selected"]
        return best

    return RetrievalResult(False, "", "none", 0.0, "", "", "", "", "", "Retrieval failed", debug_steps + ["final: retrieval_failed"])
