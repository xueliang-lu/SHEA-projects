from __future__ import annotations

import re
from typing import Any
from urllib.parse import quote_plus

from bs4 import BeautifulSoup
from mcp.server.fastmcp import FastMCP
from playwright.sync_api import sync_playwright

mcp = FastMCP("cplmcp")


def _clean_text(html: str, max_chars: int = 12000) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    text = " ".join(soup.get_text(" ").split())
    return text[:max_chars]


def _is_unit_like(url: str) -> bool:
    u = (url or "").lower()
    if not u.startswith("http"):
        return False
    bad = ["/search", "?q=", "?s=", "/news", "/events", "/about", "/contact"]
    if any(b in u for b in bad):
        return False
    good = ["/units/", "/unit/", "/subjects/", "/subject/", "/handbook/", "unit"]
    return any(g in u for g in good)


@mcp.tool()
def search_web(query: str, site: str | None = None, max_results: int = 5) -> dict[str, Any]:
    """Search the web via browser automation and return top results.

    Args:
        query: Search query
        site: Optional domain restriction, e.g. "vu.edu.au"
        max_results: Max results to return (1-10)
    """
    max_results = max(1, min(max_results, 10))
    q = query.strip()
    if site:
        q = f"site:{site} {q}"

    search_url = f"https://duckduckgo.com/?q={quote_plus(q)}"
    results: list[dict[str, str]] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(1200)

        anchors = page.locator("a[data-testid='result-title-a']")
        count = min(anchors.count(), max_results)
        for i in range(count):
            a = anchors.nth(i)
            title = (a.inner_text(timeout=1000) or "").strip()
            href = a.get_attribute("href") or ""

            snippet = ""
            try:
                snippet = (
                    page.locator("[data-result='snippet']").nth(i).inner_text(timeout=700) or ""
                ).strip()
            except Exception:
                pass

            if href:
                results.append({"title": title, "url": href, "snippet": snippet})

        browser.close()

    return {"query": q, "count": len(results), "results": results}


@mcp.tool()
def fetch_page(url: str, max_chars: int = 12000) -> dict[str, Any]:
    """Open a page with Playwright and extract readable text/title."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=45000)
        page.wait_for_timeout(900)
        html = page.content()
        title = page.title()
        browser.close()

    text = _clean_text(html, max_chars=max_chars)
    return {
        "url": url,
        "title": title,
        "text": text,
        "text_len": len(text),
    }


@mcp.tool()
def find_unit_page(
    unit_code: str,
    unit_title: str,
    institution: str,
    institution_site: str | None = None,
    max_results: int = 8,
) -> dict[str, Any]:
    """Find likely unit-level handbook pages for a unit.

    Uses browser search and filters to unit-like URLs.
    """
    query = f"{institution} {unit_code} {unit_title} unit outline handbook"
    res = search_web(query=query, site=institution_site, max_results=max_results)
    filtered = [r for r in res.get("results", []) if _is_unit_like(r.get("url", ""))]

    confidence = 0.0
    if filtered:
        top = filtered[0]
        url = top.get("url", "").lower()
        if unit_code.lower() in url:
            confidence = 0.9
        elif any(k in url for k in ["/units/", "/handbook/"]):
            confidence = 0.75
        else:
            confidence = 0.55

    return {
        "unit_code": unit_code,
        "unit_title": unit_title,
        "institution": institution,
        "institution_site": institution_site or "",
        "candidates": filtered,
        "candidate_count": len(filtered),
        "confidence": confidence,
        "status": "ok" if filtered else "no_unit_level_url_found",
    }


if __name__ == "__main__":
    mcp.run()
