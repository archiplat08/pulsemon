"""Unit tests for pulsemon/uptime.py."""
from __future__ import annotations

import sqlite3
import pytest
from datetime import datetime, timedelta

from pulsemon.db import init_db
from pulsemon.monitors import create_monitor
from pulsemon.models import Monitor
from pulsemon.uptime import (
    get_all_uptimes,
    filter_below_threshold,
    uptime_entry_as_dict,
)


@pytest.fixture()
def tmp_db():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    init_db(conn)
    yield conn
    conn.close()


def _make_monitor(conn, name="alpha", url="https://alpha.example.com"):
    m = Monitor(name=name, url=url, interval=60, timeout=10)
    return create_monitor(conn, m)


def _insert_result(conn, monitor_id, is_up, ts=None):
    if ts is None:
        ts = datetime.utcnow().isoformat()
    conn.execute(
        "INSERT INTO check_results (monitor_id, checked_at, is_up, status_code, response_ms, error)"
        " VALUES (?, ?, ?, ?, ?, ?)",
        (monitor_id, ts, int(is_up), 200 if is_up else 500, 42, None),
    )
    conn.commit()


def test_get_all_uptimes_empty_db(tmp_db):
    result = get_all_uptimes(tmp_db, days=30)
    assert result == []


def test_get_all_uptimes_no_checks(tmp_db):
    _make_monitor(tmp_db)
    result = get_all_uptimes(tmp_db, days=30)
    assert len(result) == 1
    assert result[0].uptime_pct is None


def test_get_all_uptimes_all_up(tmp_db):
    m = _make_monitor(tmp_db)
    for _ in range(5):
        _insert_result(tmp_db, m.id, is_up=True)
    result = get_all_uptimes(tmp_db, days=30)
    assert result[0].uptime_pct == pytest.approx(100.0)


def test_get_all_uptimes_mixed(tmp_db):
    m = _make_monitor(tmp_db)
    _insert_result(tmp_db, m.id, is_up=True)
    _insert_result(tmp_db, m.id, is_up=False)
    result = get_all_uptimes(tmp_db, days=30)
    assert result[0].uptime_pct == pytest.approx(50.0)


def test_filter_below_threshold_excludes_above(tmp_db):
    m = _make_monitor(tmp_db)
    for _ in range(10):
        _insert_result(tmp_db, m.id, is_up=True)
    entries = get_all_uptimes(tmp_db, days=30)
    filtered = filter_below_threshold(entries, threshold=99.0)
    assert filtered == []


def test_filter_below_threshold_includes_none(tmp_db):
    _make_monitor(tmp_db)
    entries = get_all_uptimes(tmp_db, days=30)
    filtered = filter_below_threshold(entries, threshold=99.0)
    assert len(filtered) == 1
    assert filtered[0].uptime_pct is None


def test_uptime_entry_as_dict_shape(tmp_db):
    m = _make_monitor(tmp_db)
    _insert_result(tmp_db, m.id, is_up=True)
    entries = get_all_uptimes(tmp_db, days=30)
    d = uptime_entry_as_dict(entries[0])
    assert set(d.keys()) == {"id", "name", "url", "uptime"}
    assert d["name"] == "alpha"
