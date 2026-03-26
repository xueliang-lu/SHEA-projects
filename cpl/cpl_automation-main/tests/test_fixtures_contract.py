from __future__ import annotations


REQUIRED_KEYS = {
    "student_id",
    "decision",
    "recommended_credits",
    "confidence",
    "evidence",
}


def test_expected_outputs_exist(expected_outputs: dict[str, dict], transcripts: dict[str, str]) -> None:
    assert expected_outputs, "No expected extraction JSON fixtures found"
    assert transcripts, "No transcript text fixtures found"
    assert set(expected_outputs) == set(transcripts)


def test_expected_output_schema(expected_outputs: dict[str, dict]) -> None:
    for name, payload in expected_outputs.items():
        missing = REQUIRED_KEYS - set(payload)
        assert not missing, f"{name} missing keys: {sorted(missing)}"
        assert payload["decision"] in {"approved", "partial", "rejected"}
        assert isinstance(payload["recommended_credits"], list)
        assert isinstance(payload["confidence"], (int, float))
        assert 0 <= payload["confidence"] <= 1
        assert isinstance(payload["evidence"], list)
