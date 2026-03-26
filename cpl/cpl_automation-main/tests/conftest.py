from __future__ import annotations

import json
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def fixtures_dir() -> Path:
    return Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def expected_outputs(fixtures_dir: Path) -> dict[str, dict]:
    expected_dir = fixtures_dir / "expected"
    out: dict[str, dict] = {}
    for file in expected_dir.glob("*.json"):
        out[file.stem] = json.loads(file.read_text())
    return out


@pytest.fixture(scope="session")
def transcripts(fixtures_dir: Path) -> dict[str, str]:
    transcript_dir = fixtures_dir / "transcripts"
    out: dict[str, str] = {}
    for file in transcript_dir.glob("*.txt"):
        out[file.stem] = file.read_text()
    return out
