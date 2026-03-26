"""
LLM-assisted retrieval helpers.
Author: Sunil Paudel

Optional reasoning layer for URL ranking and content structuring.
Enabled only when OPENAI_API_KEY is present.
"""

from __future__ import annotations

import json
import os
import time
from typing import Dict, List, Optional

import requests


# Safety controls to prevent runaway LLM usage/cost.
_LLM_CALL_COUNT = 0
_LLM_WINDOW_START = time.time()


def _llm_budget_available() -> bool:
    global _LLM_CALL_COUNT, _LLM_WINDOW_START
    max_calls_total = int(os.getenv("LLM_MAX_CALLS_TOTAL", "120"))
    max_calls_per_minute = int(os.getenv("LLM_MAX_CALLS_PER_MINUTE", "40"))

    now = time.time()
    if now - _LLM_WINDOW_START >= 60:
        _LLM_WINDOW_START = now
        _LLM_CALL_COUNT = 0

    if _LLM_CALL_COUNT >= max_calls_total:
        return False
    if _LLM_CALL_COUNT >= max_calls_per_minute:
        return False
    return True


def llm_enabled() -> bool:
    return bool(os.getenv("OPENAI_API_KEY")) and _llm_budget_available()


def _chat_json(system: str, user: str, timeout: int = 25) -> Optional[dict]:
    global _LLM_CALL_COUNT
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or not _llm_budget_available():
        return None

    # Lightweight Responses-style call via Chat Completions compatible endpoint.
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        "temperature": 0,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "response_format": {"type": "json_object"},
    }

    try:
        _LLM_CALL_COUNT += 1
        r = requests.post(url, headers=headers, json=payload, timeout=timeout)
        r.raise_for_status()
        data = r.json()
        content = data["choices"][0]["message"]["content"]
        return json.loads(content)
    except Exception:
        return None


def rank_urls_for_unit(unit_code: str, title: str, institution: str, urls: List[str]) -> List[str]:
    """Use LLM to prioritize likely official unit pages."""
    if not llm_enabled() or len(urls) <= 1:
        return urls

    system = (
        "You rank candidate URLs for an academic unit page. "
        "Prefer official university pages with unit handbook/outline content. "
        "Return JSON: {\"ranked_urls\": [..]} using only input URLs."
    )
    user = json.dumps(
        {
            "institution": institution,
            "unit_code": unit_code,
            "unit_title": title,
            "candidate_urls": urls,
        },
        ensure_ascii=False,
    )
    res = _chat_json(system, user)
    if not res or "ranked_urls" not in res:
        return urls

    ranked = [u for u in res.get("ranked_urls", []) if isinstance(u, str) and u in urls]
    remainder = [u for u in urls if u not in ranked]
    return ranked + remainder


def structure_unit_content(raw_text: str) -> Dict[str, str]:
    """Use LLM to structure extracted page text into target fields."""
    if not llm_enabled() or not raw_text.strip():
        return {}

    system = (
        "Extract unit details from academic page text. "
        "Return JSON keys: description, learning_outcomes, topics, credit_points, aqf_level. "
        "Use empty string when unknown. Keep concise."
    )
    user = raw_text[:9000]
    res = _chat_json(system, user, timeout=30)
    if not res:
        return {}

    out = {
        "description": str(res.get("description", "") or ""),
        "learning_outcomes": str(res.get("learning_outcomes", "") or ""),
        "topics": str(res.get("topics", "") or ""),
        "credit_points": str(res.get("credit_points", "") or ""),
        "aqf_level": str(res.get("aqf_level", "") or ""),
    }
    return out


def compare_units_natural_language(
    external_unit: Dict[str, str],
    shea_unit: Dict[str, str],
    score: float,
) -> str:
    """Natural-language comparison of two units (LLM when available, safe fallback otherwise)."""
    ext_title = str(external_unit.get("title", "") or "")
    shea_title = str(shea_unit.get("title", "") or "")
    ext_desc = str(external_unit.get("description", "") or "")
    shea_desc = str(shea_unit.get("description", "") or "")
    ext_lo = str(external_unit.get("learning_outcomes", "") or "")
    shea_lo = str(shea_unit.get("learning_outcomes", "") or "")

    if llm_enabled():
        system = (
            "You compare academic units for credit transfer. "
            "Return JSON with one key: explanation. "
            "Write 2-4 sentences in plain language with: what matches, what differs, and confidence wording."
        )
        user = json.dumps(
            {
                "external": {
                    "title": ext_title,
                    "description": ext_desc[:2200],
                    "learning_outcomes": ext_lo[:1800],
                },
                "shea": {
                    "title": shea_title,
                    "description": shea_desc[:2200],
                    "learning_outcomes": shea_lo[:1800],
                },
                "numeric_score": score,
            },
            ensure_ascii=False,
        )
        res = _chat_json(system, user, timeout=25)
        if res and str(res.get("explanation", "")).strip():
            return str(res.get("explanation")).strip()

    # Deterministic fallback when API key is not configured.
    if score >= 0.75:
        conf = "strong"
    elif score >= 0.5:
        conf = "moderate"
    else:
        conf = "low"

    return (
        f"AI-style summary: {ext_title} and {shea_title} show {conf} alignment overall (score {score:.2f}). "
        f"The comparison is based on overlap between unit descriptions and learning outcomes. "
        f"Please review specific outcome verbs and scope depth before final approval."
    )
