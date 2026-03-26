from __future__ import annotations

from importlib import import_module

import pytest


@pytest.fixture(scope="module")
def parser_module():
    try:
        return import_module("cpl_automation.parser")
    except ModuleNotFoundError as exc:
        pytest.skip(f"Missing parser module: {exc}")


def test_parse_transcript_contract(parser_module) -> None:
    assert hasattr(parser_module, "parse_transcript"), (
        "Expected cpl_automation.parser.parse_transcript(text)"
    )


def test_parse_transcript_against_fixtures(parser_module, transcripts, expected_outputs) -> None:
    parse_transcript = parser_module.parse_transcript

    for name, transcript in transcripts.items():
        result = parse_transcript(transcript)
        expected = expected_outputs[name]

        for key in ["student_id", "decision"]:
            assert result.get(key) == expected[key], f"{name}: mismatch in {key}"

        assert isinstance(result.get("recommended_credits", []), list)
        assert len(result.get("evidence", [])) >= 1
