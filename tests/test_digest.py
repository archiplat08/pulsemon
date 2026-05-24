"""Unit tests for pulsemon.digest."""
from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone

import pytest

from pulsemon.db import init_db
from pulsemon.digest import Digest, build_digest, digest_as_dict


@pytest.fixture()
def tmp_db():
    conn = sqlite3.connect(":memory:")
    init_db(conn)
    yield conn
    conn.close()


def _make_monitor(conn: sqlite3.Connection, name: str = "m1") -> int:
    cur = conn.execute(
        "INSERT INTO monitors (name, url, interval, timeout, created_at) VALUES (?,?,?,?,?)",
        (name, f"http://example.com/{name}", 60, 10, datetime.now(timezone.utc).isoformat()),
    )
    conn.commit()
    return cur.lastrowid


def _insert_result(conn, monitor_id, status, offset_hours=0):
    ts = (datetime.now(timezone.utc) - timedelta(hours=offset_hours)).isoformat()
    conn.execute(
        "INSERT INTO check_results (monitor_id, status, response_ms, checked_at) VALUES (?,?,?,?)",
        (monitor_id, status, 100, ts),
    )
    conn.commit()


def test_build_digest_empty_db(tmp_db):
    d = build_digest(tmp_db, hours=24)
    assert d.total == 0
    assert d.up == 0
    assert d.down == 0
    assert d.no_data == 0
    assert d.checks_in_window == 0
    assert d.avg_uptime_pct == 0.0


def test_build_digest_counts_up_down_no_data(tmp_db):
    mid1 = _make_monitor(tmp_db, "up-monitor")
    mid2 = _make_monitor(tmp_db, "down-monitor")
    _make_monitor(tmp_db, "no-data-monitor")

    _insert_result(tmp_db, mid1, "up")
    _insert_result(tmp_db, mid2, "down")

    d = build_digest(tmp_db, hours=24)
    assert d.total == 3
    assert d.up == 1
    assert d.down == 1
    assert d.no_data == 1


def test_build_digest_checks_in_window(tmp_db):
    mid = _make_monitor(tmp_db)
    _insert_result(tmp_db, mid, "up", offset_hours=1)
    _insert_result(tmp_db, mid, "up", offset_hours=2)
    # outside 3-hour window
    _insert_result(tmp_db, mid, "up", offset_hours=5)

    d = build_digest(tmp_db, hours=3)
    assert d.checks_in_window == 2


def test_build_digest_avg_uptime(tmp_db):
    mid = _make_monitor(tmp_db)
    _insert_result(tmp_db, mid, "up")
    _insert_result(tmp_db, mid, "up")
    _insert_result(tmp_db, mid, "down")

    d = build_digest(tmp_db, hours=24)
    assert abs(d.avg_uptime_pct - 66.67) < 0.1


def test_digest_as_dict_keys(tmp_db):
    d = build_digest(tmp_db)
    result = digest_as_dict(d)
    expected_keys = {"total", "up", "down", "no_data", "checks_in_window", "avg_uptime_pct", "incidents_opened"}
    assert set(result.keys()) == expected_keys


def test_build_digest_no_incidents_table_does_not_raise(tmp_db):
    """incidents table may not exist; digest should still work."""
    tmp_db.execute("DROP TABLE IF EXISTS incidents")
    tmp_db.commit()
    d = build_digest(tmp_db, hours=24)
    assert d.incidents_opened == 0
