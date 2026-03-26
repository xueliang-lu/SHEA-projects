from __future__ import annotations

from importlib import import_module

import csv

import pytest


@pytest.fixture(scope="module")
def export_module():
    try:
        return import_module("cpl_automation.export")
    except ModuleNotFoundError as exc:
        pytest.skip(f"Missing export module: {exc}")


def test_export_contract(export_module) -> None:
    assert hasattr(export_module, "export_applications_to_csv"), (
        "Expected cpl_automation.export.export_applications_to_csv(rows, output_path)"
    )


def test_export_csv_output(export_module, tmp_path) -> None:
    rows = [
        {
            "id": 1,
            "student_id": "STU-1001",
            "decision": "approved",
            "recommended_credits": "CPL101;CPL203",
            "updated_at": "2026-02-17T10:11:12Z",
        }
    ]

    out_path = tmp_path / "applications.csv"
    export_module.export_applications_to_csv(rows, out_path)

    with out_path.open(newline="") as f:
        reader = csv.DictReader(f)
        parsed = list(reader)

    assert len(parsed) == 1
    assert parsed[0]["student_id"] == "STU-1001"
    assert parsed[0]["decision"] == "approved"
