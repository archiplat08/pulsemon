"""Tests for pulsemon.history."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from pulsemon.db import init_db
from pulsemon.history import get_check_history, get_uptime_percentage, purge_old_results
from pulsemon.models import Monitor, CheckResult


@pytest.fixture()
def tmp_db(tmp_path):
    db_file = tmp_path / "test.db"
    with patch("pulsemon.db.DB_PATH", str(db_file)):
        init_db()
        yield str(db_file)


def _make_monitor(db_path: str) -> str:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute(
        "INSERT INTO monitors (id, name, url, interval, timeout, created_at) "
        "VALUES ('m1', 'Test', 'http://example.com', 60, 5, '2024-01-01T00:00:00')"
    )
    conn.commit()
    conn.close()
    return "m1"


def _insert_result(db_path: str, monitor_id: str, is_up: bool, offset_minutes: int = 0):
    ts = (datetime.utcnow() - timedelta(minutes=offset_minutes)).isoformat()
    conn = sqlite3.connect(db_path)
    conn.execute(
        "INSERT INTO check_results (monitor_id, checked_at, status_code, "
        "response_time_ms, is_up, error) VALUES (?, ?, ?, ?, ?, ?)",
        (monitor_id, ts, 200 if is_up else 500, 120, 1 if is_up else 0, None),
    )
    conn.commit()
    conn.close()


def test_get_check_history_returns_results(tmp_db):
    with patch("pulsemon.db.DB_PATH", tmp_db):
        mid = _make_monitor(tmp_db)
        _insert_result(tmp_db, mid, is_up=True)
        _insert_result(tmp_db, mid, is_up=False)
        results = get_check_history(mid)
    assert len(results) == 2
    assert all(isinstance(r, CheckResult) for r in results)


def test_get_check_history_respects_limit(tmp_db):
    with patch("pulsemon.db.DB_PATH", tmp_db):
        mid = _make_monitor(tmp_db)
        for _ in range(5):
            _insert_result(tmp_db, mid, is_up=True)
        results = get_check_history(mid, limit=3)
    assert len(results) == 3


def test_get_check_history_respects_since(tmp_db):
    with patch("pulsemon.db.DB_PATH", tmp_db):
        mid = _make_monitor(tmp_db)
        _insert_result(tmp_db, mid, is_up=True, offset_minutes=120)
        _insert_result(tmp_db, mid, is_up=True, offset_minutes=10)
        since = datetime.utcnow() - timedelta(minutes=30)
        results = get_check_history(mid, since=since)
    assert len(results) == 1


def test_get_uptime_percentage_all_up(tmp_db):
    with patch("pulsemon.db.DB_PATH", tmp_db):
        mid = _make_monitor(tmp_db)
        for _ in range(4):
            _insert_result(tmp_db, mid, is_up=True)
        pct = get_uptime_percentage(mid)
    assert pct == 100.0


def test_get_uptime_percentage_mixed(tmp_db):
    with patch("pulsemon.db.DB_PATH", tmp_db):
        mid = _make_monitor(tmp_db)
        _insert_result(tmp_db, mid, is_up=True)
        _insert_result(tmp_db, mid, is_up=True)
        _insert_result(tmp_db, mid, is_up=False)
        _insert_result(tmp_db, mid, is_up=False)
        pct = get_uptime_percentage(mid)
    assert pct == 50.0


def test_get_uptime_percentage_no_data(tmp_db):
    with patch("pulsemon.db.DB_PATH", tmp_db):
        mid = _make_monitor(tmp_db)
        pct = get_uptime_percentage(mid)
    assert pct is None


def test_purge_old_results_removes_old(tmp_db):
    with patch("pulsemon.db.DB_PATH", tmp_db):
        mid = _make_monitor(tmp_db)
        _insert_result(tmp_db, mid, is_up=True, offset_minutes=60 * 24 * 40)
        _insert_result(tmp_db, mid, is_up=True, offset_minutes=10)
        deleted = purge_old_results(retention_days=30)
    assert deleted == 1


def test_purge_old_results_keeps_recent(tmp_db):
    with patch("pulsemon.db.DB_PATH", tmp_db):
        mid = _make_monitor(tmp_db)
        _insert_result(tmp_db, mid, is_up=True, offset_minutes=5)
        deleted = purge_old_results(retention_days=30)
    assert deleted == 0
