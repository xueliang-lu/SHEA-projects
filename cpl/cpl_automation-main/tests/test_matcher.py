from __future__ import annotations

from importlib import import_module

import pytest


@pytest.fixture(scope="module")
def matcher_module():
    try:
        return import_module("cpl_automation.matcher")
    except ModuleNotFoundError as exc:
        pytest.skip(f"Missing matcher module: {exc}")


def test_matcher_contract(matcher_module) -> None:
    assert hasattr(matcher_module, "match_courses"), (
        "Expected cpl_automation.matcher.match_courses(extraction, catalog)"
    )


def test_matcher_recommendation_presence(matcher_module, expected_outputs) -> None:
    match_courses = matcher_module.match_courses
    extraction = expected_outputs["transcript_approved"]
    catalog = [
        {"code": "CPL101", "title": "Foundations of Prior Learning"},
        {"code": "CPL203", "title": "Applied Workplace Communication"},
    ]

    recs = match_courses(extraction, catalog)
    assert isinstance(recs, list)
    assert recs, "Matcher should return at least one recommendation"

    first = recs[0]
    assert "code" in first and "reason" in first
    if "confidence" in first:
        assert 0 <= first["confidence"] <= 1
