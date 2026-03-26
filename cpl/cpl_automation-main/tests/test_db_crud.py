from __future__ import annotations

from importlib import import_module

import pytest


@pytest.fixture(scope="module")
def db_module():
    try:
        return import_module("cpl_automation.db")
    except ModuleNotFoundError as exc:
        pytest.skip(f"Missing DB module: {exc}")


def test_db_repository_contract(db_module) -> None:
    assert hasattr(db_module, "CPLRepository"), "Expected cpl_automation.db.CPLRepository"


def test_db_crud_lifecycle(db_module, tmp_path) -> None:
    repo_cls = db_module.CPLRepository
    repo = repo_cls(tmp_path / "cpl_test.db")

    repo.init_schema()
    app_id = repo.create_application(
        student_id="STU-1001",
        transcript_id="fixture-approved",
        decision="partial",
        rationale="Initial auto-decision",
    )
    assert app_id

    fetched = repo.get_application(app_id)
    assert fetched["student_id"] == "STU-1001"
    assert fetched["decision"] == "partial"

    repo.update_decision(app_id, decision="approved", rationale="Manual confirmation")
    updated = repo.get_application(app_id)
    assert updated["decision"] == "approved"

    rows = repo.list_applications()
    assert any(row["id"] == app_id for row in rows)
