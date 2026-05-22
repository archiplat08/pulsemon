"""Tests for pulsemon database initialization and connection helpers."""

import sqlite3
import pytest
from pulsemon.db import init_db, db_conn, get_connection


@pytest.fixture
def tmp_db(tmp_path):
    """Return a path to a fresh temporary SQLite database."""
    db_path = str(tmp_path / "test_pulsemon.db")
    init_db(db_path)
    return db_path


def test_init_db_creates_tables(tmp_db):
    conn = get_connection(tmp_db)
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {row["name"] for row in cursor.fetchall()}
    assert "monitors" in tables
    assert "checks" in tables
    assert "alerts" in tables
    conn.close()


def test_init_db_is_idempotent(tmp_db):
    """Calling init_db twice should not raise or duplicate tables."""
    init_db(tmp_db)
    conn = get_connection(tmp_db)
    cursor = conn.execute(
        "SELECT COUNT(*) as cnt FROM sqlite_master WHERE type='table'"
    )
    assert cursor.fetchone()["cnt"] == 3
    conn.close()


def test_db_conn_commits_on_success(tmp_db):
    with db_conn(tmp_db) as conn:
        conn.execute(
            "INSERT INTO monitors (name, url, interval_seconds) VALUES (?, ?, ?)",
            ("Example", "https://example.com", 30),
        )

    conn2 = get_connection(tmp_db)
    row = conn2.execute("SELECT * FROM monitors WHERE name='Example'").fetchone()
    assert row is not None
    assert row["url"] == "https://example.com"
    conn2.close()


def test_db_conn_rolls_back_on_error(tmp_db):
    with pytest.raises(sqlite3.OperationalError):
        with db_conn(tmp_db) as conn:
            conn.execute("INSERT INTO nonexistent_table VALUES (1)")

    conn2 = get_connection(tmp_db)
    row = conn2.execute("SELECT COUNT(*) as cnt FROM monitors").fetchone()
    assert row["cnt"] == 0
    conn2.close()


def test_foreign_keys_enforced(tmp_db):
    with pytest.raises(sqlite3.IntegrityError):
        with db_conn(tmp_db) as conn:
            conn.execute(
                "INSERT INTO checks (monitor_id, is_up) VALUES (?, ?)",
                (9999, 1),
            )
