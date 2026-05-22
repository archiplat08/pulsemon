"""Integration test: purge interacts correctly with history queries."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from pulsemon.db import init_db
from pulsemon.history import get_check_history, get_uptime_percentage, purge_old_results


@pytest.fixture()
def tmp_db(tmp_path):
    db_file = tmp_path / "test.db"
    with patch("pulsemon.db.DB_PATH", str(db_file)):
        init_db()
        yield str(db_file)


def _insert(db_path: str, monitor_id: str, is_up: bool, offset_days: int = 0):
    ts = (datetime.utcnow() - timedelta(days=offset_days)).isoformat()
    conn = sqlite3.connect(db_path)
    conn.execute(
        "INSERT INTO monitors (id, name, url, interval, timeout, created_at) "
        "VALUES (?, 'T', 'http://t.test', 60, 5, '2024-01-01') "
        "ON CONFLICT(id) DO NOTHING",
        (monitor_id,),
    )
    conn.execute(
        "INSERT INTO check_results (monitor_id, checked_at, status_code, "
        "response_time_ms, is_up, error) VALUES (?, ?, 200, 50, ?, NULL)",
        (monitor_id, ts, 1 if is_up else 0),
    )
    conn.commit()
    conn.close()


def test_purge_then_history_empty(tmp_db):
    with patch("pulsemon.db.DB_PATH", tmp_db):
        _insert(tmp_db, "m1", True, offset_days=60)
        purge_old_results(retention_days=30)
        results = get_check_history("m1")
    assert results == []


def test_purge_then_uptime_none(tmp_db):
    with patch("pulsemon.db.DB_PATH", tmp_db):
        _insert(tmp_db, "m1", True, offset_days=60)
        purge_old_results(retention_days=30)
        pct = get_uptime_percentage("m1", window_hours=24)
    assert pct is None


def test_purge_leaves_recent_intact(tmp_db):
    with patch("pulsemon.db.DB_PATH", tmp_db):
        _insert(tmp_db, "m1", True, offset_days=1)
        _insert(tmp_db, "m1", False, offset_days=60)
        deleted = purge_old_results(retention_days=30)
        results = get_check_history("m1")
    assert deleted == 1
    assert len(results) == 1
    assert results[0].is_up is True
