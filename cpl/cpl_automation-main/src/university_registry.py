"""
University registry helpers.
Author: Sunil Paudel

Stores known institution -> website URLs for enrichment routing.
Now DB-backed (institution_registry table) with JSON legacy migration.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from .db import init_db, fetch_institution_registry_rows, upsert_institution_registry_rows


BASE_DIR = Path(__file__).resolve().parent.parent
REGISTRY_PATH = BASE_DIR / "data" / "university_registry.json"


def _normalize_registry(reg: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for k, v in reg.items():
        name = str(k).strip()
        if not name:
            continue
        if isinstance(v, str):
            url = v.strip()
            if url:
                out[name] = url
        elif isinstance(v, dict):
            vv = {
                str(kk).strip().lower(): str(vv).strip()
                for kk, vv in v.items()
                if str(vv).strip()
            }
            if vv:
                out[name] = vv
    return out


def _load_registry_from_json(path: Path = REGISTRY_PATH) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return _normalize_registry(data)
    except Exception:
        pass
    return {}


def _flatten_for_db(registry: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for name, value in registry.items():
        if isinstance(value, str):
            rows.append(
                {
                    "institution_name": name,
                    "qualification": "",
                    "base_url": value,
                    "is_active": 1,
                }
            )
        elif isinstance(value, dict):
            for q, url in value.items():
                if url:
                    rows.append(
                        {
                            "institution_name": name,
                            "qualification": str(q).lower(),
                            "base_url": str(url),
                            "is_active": 1,
                        }
                    )
    return rows


def _load_registry_from_db() -> Dict[str, Any]:
    init_db()
    rows = fetch_institution_registry_rows()
    out: Dict[str, Any] = {}
    for r in rows:
        name = str(r["institution_name"]).strip()
        q = str(r["qualification"] or "").strip().lower()
        url = str(r["base_url"] or "").strip()
        if not name or not url:
            continue
        if not q:
            out[name] = url
        else:
            existing = out.get(name)
            if isinstance(existing, str):
                out[name] = {q: url}
            elif isinstance(existing, dict):
                existing[q] = url
            else:
                out[name] = {q: url}
    return out


def load_registry(path: Path = REGISTRY_PATH) -> Dict[str, Any]:
    # Primary source: DB
    db_registry = _load_registry_from_db()
    if db_registry:
        return db_registry

    # One-time migration fallback from legacy JSON.
    json_registry = _load_registry_from_json(path)
    if json_registry:
        upsert_institution_registry_rows(_flatten_for_db(json_registry))
        return _load_registry_from_db()

    return {}


def save_registry(registry: Dict[str, Any], path: Path = REGISTRY_PATH) -> None:
    # Save into DB (primary runtime source)
    normalized = _normalize_registry(registry)
    upsert_institution_registry_rows(_flatten_for_db(normalized))

    # Also mirror to JSON for backward compatibility / manual inspection.
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(normalized, indent=2, ensure_ascii=False), encoding="utf-8")
