"""
CPL Automation System
Author: Sunil Paudel

Notes:
- Mandatory step: run AI retrieval first. All external units must be enriched via Playwright before matching.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List

from .retrieval_agent import _strip_html, harvest_shea_units_for_qualification  # reuse sanitizer
import pandas as pd
import requests

SHEA_BIT_URL = "https://shea.edu.au/courses/bachelor-of-information-technology/"
SHEA_MIT_URL = "https://shea.edu.au/courses/master-of-information-technology/"
DEFAULT_SHEA_XLSX_PATH = Path("data/SHEA Course Data.xlsx")


def _fetch_text(url: str) -> str:
    r = requests.get(url, timeout=25, headers={"User-Agent": "Mozilla/5.0"})
    r.raise_for_status()
    return _strip_html(r.text)


def _extract_aqf(text: str) -> str:
    m = re.search(r"aqf\s*level\s*[:]?\s*(\d{1,2})", text, flags=re.I)
    return m.group(1) if m else ""


def _extract_units(text: str, course: str, aqf: str) -> List[Dict[str, Any]]:
    units: List[Dict[str, Any]] = []
    seen = set()
    # Code-like tokens seen in SHEA pages (e.g., ITOP501, PROF910)
    pattern = re.compile(r"\b([A-Z]{4,5}\d{3})\b\s+(.+?)(?=\b[A-Z]{4,5}\d{3}\b|$)", flags=re.S)
    for m in pattern.finditer(text):
        code = m.group(1).strip()
        raw_title = " ".join(m.group(2).split())
        # trim known section labels/noise that may trail after title
        raw_title = re.split(r"\b(Trimester|Year|Core|Elective|Choose|Table|Mode of Delivery)\b", raw_title, maxsplit=1, flags=re.I)[0]
        title = raw_title.strip(" -:,")[:120]
        if code in seen:
            continue
        seen.add(code)
        units.append(
            {
                "unit_code": code,
                "title": title,
                "description": f"Imported from SHEA {course} course page",
                "learning_outcomes": "",
                "aqf_level": aqf,
                "course": course,
                "credit_points": "",
                "keywords": "",
            }
        )
    return units


def _clean_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).replace("\u202f", " ").replace("\xa0", " ").strip()
    return "" if text.lower() == "nan" else " ".join(text.split())


def load_shea_units_from_excel(xlsx_path: Path = DEFAULT_SHEA_XLSX_PATH) -> List[Dict[str, Any]]:
    if not xlsx_path.exists():
        raise FileNotFoundError(f"SHEA data file not found: {xlsx_path}")

    df = pd.read_excel(xlsx_path, sheet_name="Course Outlines")
    units: List[Dict[str, Any]] = []
    course = "BIT"

    for _, row in df.iterrows():
        first = _clean_text(row.iloc[0] if len(row) > 0 else "")
        trimester = _clean_text(row.iloc[1] if len(row) > 1 else "")
        code = _clean_text(row.iloc[2] if len(row) > 2 else "").upper()
        title = _clean_text(row.iloc[3] if len(row) > 3 else "")
        description = _clean_text(row.iloc[4] if len(row) > 4 else "")
        outcomes = _clean_text(row.iloc[5] if len(row) > 5 else "")

        if first.upper() == "MIT":
            course = "MIT"
            continue

        if code in {"", "CODE"}:
            continue

        if not re.match(r"^[A-Z]{4,5}\d{3}$", code):
            continue

        aqf = "9" if course == "MIT" else "7"
        keywords = " ".join([trimester, first]).strip()

        units.append(
            {
                "unit_code": code,
                "title": title or code,
                "description": description,
                "learning_outcomes": outcomes,
                "aqf_level": aqf,
                "course": course,
                "credit_points": "",
                "keywords": keywords,
            }
        )

    # Deduplicate by unit_code (keep entry with richer content)
    merged: Dict[str, Dict[str, Any]] = {}
    for u in units:
        code = u["unit_code"]
        existing = merged.get(code)
        if not existing:
            merged[code] = u
            continue
        new_len = len(u.get("description", "")) + len(u.get("learning_outcomes", ""))
        old_len = len(existing.get("description", "")) + len(existing.get("learning_outcomes", ""))
        if new_len > old_len:
            merged[code] = u

    return list(merged.values())


def load_shea_units_live() -> List[Dict[str, Any]]:
    all_units: List[Dict[str, Any]] = []

    bit_text = _fetch_text(SHEA_BIT_URL)
    bit_aqf = _extract_aqf(bit_text)
    all_units.extend(_extract_units(bit_text, course="BIT", aqf=bit_aqf))

    mit_text = _fetch_text(SHEA_MIT_URL)
    mit_aqf = _extract_aqf(mit_text)
    all_units.extend(_extract_units(mit_text, course="MIT", aqf=mit_aqf))

    # Enrich SHEA units with unit-page description + learning outcomes.
    bit_details = harvest_shea_units_for_qualification("bachelor", request_timeout_seconds=12, max_workers=6)
    mit_details = harvest_shea_units_for_qualification("master", request_timeout_seconds=12, max_workers=6)

    for u in all_units:
        code = str(u.get("unit_code") or "").upper()
        detail = bit_details.get(code) if str(u.get("course") or "").upper() == "BIT" else mit_details.get(code)
        if detail:
            if detail.get("description"):
                u["description"] = detail.get("description", "")
            if detail.get("learning_outcomes"):
                u["learning_outcomes"] = detail.get("learning_outcomes", "")

    # dedupe by code, prefer non-empty descriptions/titles
    merged: Dict[str, Dict[str, Any]] = {}
    for u in all_units:
        existing = merged.get(u["unit_code"])
        if not existing:
            merged[u["unit_code"]] = u
            continue
        choose_u = (
            len(str(u.get("learning_outcomes", ""))) + len(str(u.get("description", "")))
            > len(str(existing.get("learning_outcomes", ""))) + len(str(existing.get("description", "")))
        ) or (len(str(u.get("title", ""))) > len(str(existing.get("title", ""))))
        if choose_u:
            merged[u["unit_code"]] = u

    return list(merged.values())
