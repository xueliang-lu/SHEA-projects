"""SQLite schema + data access layer for CPL MVP.
Author: Sunil Paudel
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterable, List


DB_PATH = Path("data/cpl.db")


@contextmanager
def get_conn(db_path: Path = DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def _ensure_column(conn: sqlite3.Connection, table: str, column: str, ddl: str) -> None:
    cols = {row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    if column not in cols:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {ddl}")


def init_db(db_path: Path = DB_PATH) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with get_conn(db_path) as conn:
        cur = conn.cursor()
        cur.executescript(
            """
            CREATE TABLE IF NOT EXISTS shea_units (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                unit_code TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                learning_outcomes TEXT,
                aqf_level TEXT,
                course TEXT,
                credit_points TEXT,
                keywords TEXT
            );

            CREATE TABLE IF NOT EXISTS external_units (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT,
                institution TEXT,
                unit_code TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                grade TEXT,
                year_semester TEXT,
                learning_outcomes TEXT,
                topics TEXT,
                credit_points TEXT,
                aqf_level TEXT,
                source_url TEXT,
                retrieval_mode TEXT,
                retrieval_confidence REAL,
                transcript_ref TEXT
            );

            CREATE TABLE IF NOT EXISTS suggestions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                external_unit_id INTEGER NOT NULL,
                shea_unit_id INTEGER NOT NULL,
                score REAL NOT NULL,
                confidence_band TEXT NOT NULL,
                explanation TEXT,
                name_sim REAL,
                desc_sim REAL,
                outcomes_sim REAL,
                credit_sim REAL,
                grade_bonus REAL,
                retrieval_bonus REAL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(external_unit_id) REFERENCES external_units(id),
                FOREIGN KEY(shea_unit_id) REFERENCES shea_units(id)
            );

            CREATE TABLE IF NOT EXISTS decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                suggestion_id INTEGER NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('approved', 'rejected', 'needs_review', 'override')),
                override_shea_unit_id INTEGER,
                reviewer TEXT,
                notes TEXT,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(suggestion_id) REFERENCES suggestions(id),
                FOREIGN KEY(override_shea_unit_id) REFERENCES shea_units(id)
            );

            CREATE TABLE IF NOT EXISTS external_unit_url_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                institution TEXT,
                unit_code TEXT NOT NULL,
                unit_title TEXT,
                source_url TEXT NOT NULL,
                confidence REAL,
                retrieval_mode TEXT,
                last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(institution, unit_code)
            );

            CREATE TABLE IF NOT EXISTS institution_registry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                institution_name TEXT NOT NULL,
                qualification TEXT NOT NULL DEFAULT '',
                base_url TEXT NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(institution_name, qualification)
            );
            """
        )

        # lightweight migration for existing DBs
        _ensure_column(conn, "external_units", "institution", "institution TEXT")
        _ensure_column(conn, "shea_units", "learning_outcomes", "learning_outcomes TEXT")
        _ensure_column(conn, "shea_units", "aqf_level", "aqf_level TEXT")
        _ensure_column(conn, "shea_units", "course", "course TEXT")
        _ensure_column(conn, "shea_units", "credit_points", "credit_points TEXT")
        _ensure_column(conn, "external_units", "grade", "grade TEXT")
        _ensure_column(conn, "external_units", "year_semester", "year_semester TEXT")
        _ensure_column(conn, "external_units", "learning_outcomes", "learning_outcomes TEXT")
        _ensure_column(conn, "external_units", "topics", "topics TEXT")
        _ensure_column(conn, "external_units", "credit_points", "credit_points TEXT")
        _ensure_column(conn, "external_units", "aqf_level", "aqf_level TEXT")
        _ensure_column(conn, "external_units", "source_url", "source_url TEXT")
        _ensure_column(conn, "external_units", "retrieval_mode", "retrieval_mode TEXT")
        _ensure_column(conn, "external_units", "retrieval_confidence", "retrieval_confidence REAL")
        _ensure_column(conn, "decisions", "override_shea_unit_id", "override_shea_unit_id INTEGER")
        _ensure_column(conn, "suggestions", "name_sim", "name_sim REAL")
        _ensure_column(conn, "suggestions", "desc_sim", "desc_sim REAL")
        _ensure_column(conn, "suggestions", "outcomes_sim", "outcomes_sim REAL")
        _ensure_column(conn, "suggestions", "credit_sim", "credit_sim REAL")
        _ensure_column(conn, "suggestions", "grade_bonus", "grade_bonus REAL")
        _ensure_column(conn, "suggestions", "retrieval_bonus", "retrieval_bonus REAL")


def upsert_shea_units(units: Iterable[Dict[str, Any]], db_path: Path = DB_PATH) -> None:
    with get_conn(db_path) as conn:
        conn.executemany(
            """
            INSERT INTO shea_units (unit_code, title, description, learning_outcomes, aqf_level, course, credit_points, keywords)
            VALUES (:unit_code, :title, :description, :learning_outcomes, :aqf_level, :course, :credit_points, :keywords)
            ON CONFLICT(unit_code) DO UPDATE SET
                title=excluded.title,
                description=excluded.description,
                learning_outcomes=excluded.learning_outcomes,
                aqf_level=excluded.aqf_level,
                course=excluded.course,
                credit_points=excluded.credit_points,
                keywords=excluded.keywords
            """,
            list(units),
        )


def insert_external_units(units: Iterable[Dict[str, Any]], db_path: Path = DB_PATH) -> List[int]:
    inserted_ids: List[int] = []
    with get_conn(db_path) as conn:
        cur = conn.cursor()
        for row in units:
            cur.execute(
                """
                INSERT INTO external_units (
                    source, institution, unit_code, title, description, grade, year_semester,
                    learning_outcomes, topics, credit_points, aqf_level, source_url,
                    retrieval_mode, retrieval_confidence, transcript_ref
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row.get("source"),
                    row.get("institution"),
                    row.get("unit_code"),
                    row.get("title"),
                    row.get("description"),
                    row.get("grade"),
                    row.get("year_semester"),
                    row.get("learning_outcomes"),
                    row.get("topics"),
                    row.get("credit_points"),
                    row.get("aqf_level"),
                    row.get("source_url"),
                    row.get("retrieval_mode"),
                    row.get("retrieval_confidence"),
                    row.get("transcript_ref"),
                ),
            )
            inserted_ids.append(cur.lastrowid)
    return inserted_ids


def update_external_unit_enrichment(external_unit_id: int, payload: Dict[str, Any], db_path: Path = DB_PATH) -> None:
    with get_conn(db_path) as conn:
        conn.execute(
            """
            UPDATE external_units
            SET description = COALESCE(?, description),
                learning_outcomes = COALESCE(?, learning_outcomes),
                topics = COALESCE(?, topics),
                credit_points = COALESCE(?, credit_points),
                aqf_level = COALESCE(?, aqf_level),
                source_url = COALESCE(?, source_url),
                retrieval_mode = COALESCE(?, retrieval_mode),
                retrieval_confidence = COALESCE(?, retrieval_confidence)
            WHERE id = ?
            """,
            (
                payload.get("description"),
                payload.get("learning_outcomes"),
                payload.get("topics"),
                payload.get("credit_points"),
                payload.get("aqf_level"),
                payload.get("source_url"),
                payload.get("retrieval_mode"),
                payload.get("retrieval_confidence"),
                external_unit_id,
            ),
        )


def clear_shea_units(db_path: Path = DB_PATH) -> None:
    with get_conn(db_path) as conn:
        conn.execute("DELETE FROM shea_units")


def clear_external_units(db_path: Path = DB_PATH) -> None:
    with get_conn(db_path) as conn:
        conn.execute("DELETE FROM external_units")


def clear_suggestions(db_path: Path = DB_PATH) -> None:
    with get_conn(db_path) as conn:
        conn.execute("DELETE FROM suggestions")


def insert_suggestions(rows: Iterable[Dict[str, Any]], db_path: Path = DB_PATH) -> None:
    with get_conn(db_path) as conn:
        conn.executemany(
            """
            INSERT INTO suggestions (
                external_unit_id, shea_unit_id, score, confidence_band, explanation,
                name_sim, desc_sim, outcomes_sim, credit_sim, grade_bonus, retrieval_bonus
            )
            VALUES (
                :external_unit_id, :shea_unit_id, :score, :confidence_band, :explanation,
                :name_sim, :desc_sim, :outcomes_sim, :credit_sim, :grade_bonus, :retrieval_bonus
            )
            """,
            list(rows),
        )


def upsert_decision(
    suggestion_id: int,
    status: str,
    reviewer: str = "",
    notes: str = "",
    override_shea_unit_id: int | None = None,
    db_path: Path = DB_PATH,
) -> None:
    with get_conn(db_path) as conn:
        try:
            conn.execute(
                """
                INSERT INTO decisions (suggestion_id, status, override_shea_unit_id, reviewer, notes)
                VALUES (?, ?, ?, ?, ?)
                """,
                (suggestion_id, status, override_shea_unit_id, reviewer, notes),
            )
        except sqlite3.IntegrityError:
            # Backward-compatible fallback for older DB CHECK constraint without 'override'.
            fallback_status = "needs_review" if status == "override" else status
            conn.execute(
                """
                INSERT INTO decisions (suggestion_id, status, override_shea_unit_id, reviewer, notes)
                VALUES (?, ?, ?, ?, ?)
                """,
                (suggestion_id, fallback_status, override_shea_unit_id, reviewer, notes),
            )


def fetch_suggestions(db_path: Path = DB_PATH):
    with get_conn(db_path) as conn:
        return conn.execute(
            """
            SELECT
                s.id AS suggestion_id,
                eu.unit_code AS external_unit_code,
                eu.title AS external_title,
                eu.retrieval_mode AS retrieval_mode,
                eu.source_url AS source_url,
                su.unit_code AS shea_unit_code,
                su.title AS shea_title,
                COALESCE(su.description, '') AS shea_description,
                COALESCE(su.learning_outcomes, '') AS shea_learning_outcomes,
                COALESCE(eu.description, '') AS external_description,
                COALESCE(eu.learning_outcomes, '') AS external_learning_outcomes,
                s.score,
                ROUND(s.score * 100.0, 1) AS confidence_percent,
                s.confidence_band,
                s.explanation,
                ROUND(COALESCE(s.name_sim,0) * 100.0, 1) AS name_sim_pct,
                ROUND(COALESCE(s.desc_sim,0) * 100.0, 1) AS desc_sim_pct,
                ROUND(COALESCE(s.outcomes_sim,0) * 100.0, 1) AS outcomes_sim_pct,
                ROUND(COALESCE(s.credit_sim,0) * 100.0, 1) AS credit_sim_pct,
                ROUND(COALESCE(s.grade_bonus,0) * 100.0, 1) AS grade_bonus_pct,
                ROUND(COALESCE(s.retrieval_bonus,0) * 100.0, 1) AS retrieval_bonus_pct,
                COALESCE(d.status, 'pending') AS decision_status,
                COALESCE(ov.unit_code, '') AS override_shea_unit_code,
                COALESCE(d.reviewer, '') AS reviewer,
                COALESCE(d.notes, '') AS notes
            FROM suggestions s
            JOIN external_units eu ON eu.id = s.external_unit_id
            JOIN shea_units su ON su.id = s.shea_unit_id
            LEFT JOIN decisions d ON d.suggestion_id = s.id
            LEFT JOIN shea_units ov ON ov.id = d.override_shea_unit_id
            ORDER BY s.score DESC
            """
        ).fetchall()


def fetch_shea_units(db_path: Path = DB_PATH):
    with get_conn(db_path) as conn:
        return conn.execute("SELECT * FROM shea_units ORDER BY unit_code").fetchall()


def fetch_external_units(db_path: Path = DB_PATH):
    with get_conn(db_path) as conn:
        return conn.execute("SELECT * FROM external_units ORDER BY id DESC").fetchall()


def get_cached_unit_url(institution: str, unit_code: str, db_path: Path = DB_PATH) -> str:
    with get_conn(db_path) as conn:
        row = conn.execute(
            """
            SELECT source_url
            FROM external_unit_url_cache
            WHERE lower(coalesce(institution, '')) = lower(?)
              AND lower(unit_code) = lower(?)
            ORDER BY last_seen DESC
            LIMIT 1
            """,
            (institution or "", unit_code or ""),
        ).fetchone()
        return str(row["source_url"]) if row and row["source_url"] else ""


def upsert_cached_unit_url(
    institution: str,
    unit_code: str,
    unit_title: str,
    source_url: str,
    confidence: float,
    retrieval_mode: str,
    db_path: Path = DB_PATH,
) -> None:
    if not (unit_code and source_url):
        return

    with get_conn(db_path) as conn:
        conn.execute(
            """
            INSERT INTO external_unit_url_cache (institution, unit_code, unit_title, source_url, confidence, retrieval_mode, last_seen)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(institution, unit_code) DO UPDATE SET
                unit_title=excluded.unit_title,
                source_url=excluded.source_url,
                confidence=excluded.confidence,
                retrieval_mode=excluded.retrieval_mode,
                last_seen=CURRENT_TIMESTAMP
            """,
            (
                institution or "",
                unit_code,
                unit_title or "",
                source_url,
                float(confidence or 0.0),
                retrieval_mode or "",
            ),
        )


def upsert_institution_registry_rows(rows: List[Dict[str, Any]], db_path: Path = DB_PATH) -> None:
    if not rows:
        return
    with get_conn(db_path) as conn:
        conn.executemany(
            """
            INSERT INTO institution_registry (institution_name, qualification, base_url, is_active, updated_at)
            VALUES (:institution_name, :qualification, :base_url, :is_active, CURRENT_TIMESTAMP)
            ON CONFLICT(institution_name, qualification) DO UPDATE SET
                base_url=excluded.base_url,
                is_active=excluded.is_active,
                updated_at=CURRENT_TIMESTAMP
            """,
            rows,
        )


def fetch_institution_registry_rows(db_path: Path = DB_PATH):
    with get_conn(db_path) as conn:
        return conn.execute(
            """
            SELECT institution_name, qualification, base_url, is_active
            FROM institution_registry
            WHERE is_active = 1
            ORDER BY institution_name, qualification
            """
        ).fetchall()
