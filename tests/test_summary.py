"""Tests for pulsemon.summary."""
from __future__ import annotations

import sqlite3
import time
from pathlib import Path

import pytest

from pulsemon.db import init_db
from pulsemon.models import Monitor
from pulsemon.monitors import create_monitor
from pulsemon.summary import build_overview, build_all_overviews, overview_as_dict


@pytest.fixture()
def tmp_db() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    init_db(conn)
    yield conn
    conn.close()


def _make_monitor(conn: sqlite3.Connection, name: str = "test") -> Monitor:
    return create_monitor(conn, name=name, url="https://example.com", interval=60, timeout=10)


def _insert_result(conn: sqlite3.Connection, monitor_id: int, status: str, latency: float = 50.0):
    conn.execute(
        "INSERT INTO check_results (monitor_id, checked_at, status, latency_ms, status_code, error)"
        " VALUES (?, ?, ?, ?, ?, ?)",
        (monitor_id, time.time(), status, latency, 200 if status == "up" else None, None),
    )
    conn.commit()


def test_build_overview_no_checks(tmp_db: sqlite3.Connection):
    m = _make_monitor(tmp_db)
    ov = build_overview(tmp_db, m.id)
    assert ov.monitor_id == m.id
    assert ov.name == m.name
    assert ov.status is None
    assert ov.latency_ms is None
    assert ov.uptime_24h is None
    assert ov.uptime_7d is None


def test_build_overview_with_checks(tmp_db: sqlite3.Connection):
    m = _make_monitor(tmp_db)
    _insert_result(tmp_db, m.id, "up", latency=42.0)
    ov = build_overview(tmp_db, m.id)
    assert ov.status == "up"
    assert ov.latency_ms == pytest.approx(42.0)
    assert ov.uptime_24h == pytest.approx(100.0)


def test_build_overview_unknown_monitor_raises(tmp_db: sqlite3.Connection):
    with pytest.raises(ValueError, match="not found"):
        build_overview(tmp_db, 9999)


def test_build_all_overviews_empty(tmp_db: sqlite3.Connection):
    result = build_all_overviews(tmp_db)
    assert result == []


def test_build_all_overviews_multiple(tmp_db: sqlite3.Connection):
    _make_monitor(tmp_db, name="alpha")
    _make_monitor(tmp_db, name="beta")
    result = build_all_overviews(tmp_db)
    assert len(result) == 2
    names = {o.name for o in result}
    assert names == {"alpha", "beta"}


def test_overview_as_dict_keys(tmp_db: sqlite3.Connection):
    m = _make_monitor(tmp_db)
    ov = build_overview(tmp_db, m.id)
    d = overview_as_dict(ov)
    assert set(d.keys()) == {"monitor_id", "name", "url", "status", "latency_ms", "uptime_24h", "uptime_7d"}
