"""Workflow helpers for transcript parsing and DB wiring.
Author: Sunil Paudel
"""

from __future__ import annotations

import re
from typing import Any, Dict, List

GRADE_TOKENS = {
    "hd",
    "high distinction",
    "distinction",
    "credit",
    "pass",
    "fail",
    "cr",
    "dn",
    "ps",
    "fl",
}


def detect_institution(text: str) -> tuple[str, float]:
    """Detect institution from transcript/header text with confidence.

    Strategy:
    1) explicit org keywords (university/institute/college/...)
    2) common AU institution abbreviations/full names
    3) nearby context around 'academic transcript' style headings
    """
    lines = [" ".join(l.strip().split()) for l in text.splitlines() if l.strip()]
    top = lines[:80]

    org_keywords = [
        "university",
        "institute",
        "college",
        "tafe",
        "polytechnic",
        "higher education",
    ]

    # Common abbreviations and brand names seen in AU transcripts
    known_aliases = {
        "uts": "University of Technology Sydney",
        "unsw": "University of New South Wales",
        "usyd": "The University of Sydney",
        "uq": "The University of Queensland",
        "qut": "Queensland University of Technology",
        "rmit": "RMIT University",
        "anu": "Australian National University",
        "deakin": "Deakin University",
        "monash": "Monash University",
        "federation university": "Federation University Australia",
        "federation": "Federation University Australia",
        "latrobe": "La Trobe University",
        "macquarie": "Macquarie University",
        "wollongong": "University of Wollongong",
        "griffith": "Griffith University",
        "curtin": "Curtin University",
        "swinburne": "Swinburne University of Technology",
        "victoria university": "Victoria University",
    }

    candidates: list[tuple[str, float]] = []

    # 1) explicit keyword matches
    for idx, line in enumerate(top):
        ll = line.lower()
        if any(k in ll for k in org_keywords):
            # penalize obviously non-institution lines
            if any(bad in ll for bad in ["student", "transcript", "course", "subject", "semester"]):
                base = 0.68
            else:
                base = 0.88
            if idx <= 10:
                base += 0.06
            candidates.append((line[:200], min(base, 0.95)))

    # 2) alias matches
    for idx, line in enumerate(top):
        ll = line.lower()
        for alias, canonical in known_aliases.items():
            if re.search(rf"\b{re.escape(alias)}\b", ll):
                base = 0.74 if len(alias) <= 4 else 0.82
                if idx <= 12:
                    base += 0.08
                candidates.append((canonical, min(base, 0.93)))

    # 3) find line near 'academic transcript'
    for idx, line in enumerate(top):
        ll = line.lower()
        if "academic transcript" in ll or ll.strip() == "transcript":
            for j in range(max(0, idx - 3), min(len(top), idx + 3)):
                nl = top[j].lower()
                if any(k in nl for k in org_keywords):
                    candidates.append((top[j][:200], 0.9))

    if not candidates:
        return "", 0.0

    # pick highest confidence; prefer longer/more specific names on ties
    candidates.sort(key=lambda x: (x[1], len(x[0])), reverse=True)
    name, conf = candidates[0]
    return name.strip(), conf


def _extract_term(line: str) -> str:
    m = re.search(r"(semester\s*[12]|trimester\s*[123]|term\s*[123]).{0,15}(20\d{2})", line, flags=re.I)
    if m:
        return f"{m.group(1).title()} {m.group(2)}"
    m2 = re.search(r"(20\d{2}).{0,15}(semester\s*[12]|trimester\s*[123]|term\s*[123])", line, flags=re.I)
    if m2:
        return f"{m2.group(2).title()} {m2.group(1)}"
    return ""


def _extract_grade(text: str) -> str:
    clean = text.strip().lower()
    # prefer long labels first
    for token in ["high distinction", "distinction", "credit", "pass", "fail"]:
        if re.search(rf"\b{re.escape(token)}\b", clean):
            return token.title()

    # common short forms
    alias_map = {
        "HD": "HD",
        "DN": "Distinction",
        "DI": "Distinction",
        "D": "Distinction",
        "CR": "Credit",
        "C": "Credit",
        "PS": "Pass",
        "PP": "Pass",
        "P": "Pass",
        "FL": "Fail",
        "NN": "Fail",
        "F": "Fail",
    }

    # Highest precision: grades near delimiters like "73 / D 12" or trailing "- C"
    m = re.search(r"(?:/|\||-|:)\s*(HD|DN|DI|D|CR|C|PS|PP|P|FL|NN|F)\b", text, flags=re.I)
    if m:
        return alias_map.get(m.group(1).upper(), "")

    for token, label in alias_map.items():
        if re.search(rf"\b{token}\b", text, flags=re.I):
            return label

    return ""


def parse_external_units_from_text(text: str, source: str = "transcript") -> List[Dict[str, Any]]:
    """Parse transcript text into external units with richer fields.

    Supports common line patterns like:
    - COSC101 - Introduction to Programming - Credit
    - COSC202 Data Structures Distinction
    - Semester 1 2024  (context line applied to subsequent units)
    """
    units: List[Dict[str, Any]] = []
    seen_codes = set()
    institution, _ = detect_institution(text)
    current_term = ""

    for line in text.splitlines():
        clean = " ".join(line.strip().split())
        if not clean:
            continue

        maybe_term = _extract_term(clean)
        if maybe_term:
            current_term = maybe_term
            continue

        match = re.match(r"^([A-Z]{2,6}\d{2,4})\s*[-:]?\s*(.+)$", clean)
        if not match:
            continue

        code, rest = match.group(1), match.group(2)
        if code in seen_codes:
            continue

        # split by dashes/pipes to isolate title and grade-like suffix
        parts = [p.strip() for p in re.split(r"\s*[-|–—]\s*", rest) if p.strip()]
        title = parts[0] if parts else rest

        grade = ""
        # search in explicit tail sections first
        for p in parts[1:]:
            g = _extract_grade(p)
            if g:
                grade = g
                break
        if not grade:
            grade = _extract_grade(rest)

        # clean title if grade token was inline at end
        title = re.sub(r"\b(HD|DN|DI|D|CR|C|PS|PP|P|FL|NN|F|High Distinction|Distinction|Credit|Pass|Fail)\b\s*$", "", title, flags=re.I).strip(" -:,/|")

        seen_codes.add(code)
        units.append(
            {
                "source": source,
                "institution": institution,
                "unit_code": code,
                "title": title[:200],
                "description": f"Extracted from transcript line: {clean[:500]}",
                "grade": grade,
                "year_semester": current_term,
                "aqf_level": "",
                "transcript_ref": source,
            }
        )

    return units


def rows_to_dicts(rows) -> List[Dict[str, Any]]:
    return [dict(r) for r in rows]
