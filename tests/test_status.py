"""Tests for pulsemon/status.py"""
import sqlite3
import uuid
from datetime import datetime, timezone

import pytest

from pulsemon.db import init_db
from pulsemon.monitors import create_monitor
from pulsemon.checks import save_check_result
from pulsemon.models import Monitor, CheckResult
from pulsemon.status import get_monitor_status, get_all_statuses, status_as_dict


@pytest.fixture
def tmp_db(tmp_path):
    db_file = tmp_path / "test.db"
    conn = sqlite3.connect(str(db_file))
    conn.row_factory = sqlite3.Row
    init_db(conn)
    yield conn
    conn.close()


def _make_monitor(conn, name="Test", url="https://example.com", interval=60):
    m = Monitor(id=None, name=name, url=url, interval=interval, timeout=5)
    return create_monitor(conn, m)


def _insert_result(conn, monitor_id, is_up=True, status_code=200, response_ms=42.0):
    r = CheckResult(
        id=None,
        monitor_id=monitor_id,
        checked_at=datetime.now(timezone.utc).isoformat(),
        is_up=is_up,
        status_code=status_code,
        response_ms=response_ms,
        error=None,
    )
    save_check_result(conn, r)


def test_get_monitor_status_no_checks(tmp_db):
    m = _make_monitor(tmp_db)
    status = get_monitor_status(tmp_db, m.id)
    assert status is not None
    assert status.monitor_id == m.id
    assert status.is_up is None
    assert status.last_checked_at is None
    assert status.uptime_24h is None


def test_get_monitor_status_with_check(tmp_db):
    m = _make_monitor(tmp_db)
    _insert_result(tmp_db, m.id, is_up=True, status_code=200, response_ms=55.0)
    status = get_monitor_status(tmp_db, m.id)
    assert status.is_up is True
    assert status.last_status_code == 200
    assert status.last_response_ms == 55.0
    assert status.uptime_24h == 100.0


def test_get_monitor_status_unknown_id(tmp_db):
    result = get_monitor_status(tmp_db, "nonexistent-id")
    assert result is None


def test_get_all_statuses_empty(tmp_db):
    statuses = get_all_statuses(tmp_db)
    assert statuses == []


def test_get_all_statuses_multiple(tmp_db):
    m1 = _make_monitor(tmp_db, name="Alpha", url="https://alpha.example.com")
    m2 = _make_monitor(tmp_db, name="Beta", url="https://beta.example.com")
    _insert_result(tmp_db, m1.id, is_up=True)
    statuses = get_all_statuses(tmp_db)
    assert len(statuses) == 2
    ids = {s.monitor_id for s in statuses}
    assert m1.id in ids and m2.id in ids


def test_status_as_dict_keys(tmp_db):
    m = _make_monitor(tmp_db)
    _insert_result(tmp_db, m.id, is_up=False, status_code=500)
    status = get_monitor_status(tmp_db, m.id)
    d = status_as_dict(status)
    expected_keys = {
        "monitor_id", "name", "url", "is_up",
        "last_checked_at", "uptime_24h",
        "last_status_code", "last_response_ms",
    }
    assert set(d.keys()) == expected_keys
    assert d["is_up"] is False
    assert d["last_status_code"] == 500
