"""Unit tests for pulsemon.snapshot."""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

import pytest

from pulsemon.db import init_db
from pulsemon.models import Monitor
from pulsemon.monitors import create_monitor
from pulsemon.checks import save_check_result
from pulsemon.models import CheckResult
from pulsemon.snapshot import take_snapshot, snapshot_as_dict, snapshot_summary_line


@pytest.fixture()
def tmp_db():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    init_db(conn)
    yield conn
    conn.close()


def _make_monitor(conn, name="alpha", url="https://alpha.example.com") -> Monitor:
    return create_monitor(conn, name=name, url=url, interval=60, timeout=5)


def _insert_result(conn, monitor_id: int, *, is_up: bool, status_code: int = 200):
    result = CheckResult(
        monitor_id=monitor_id,
        checked_at=datetime.now(timezone.utc).isoformat(),
        is_up=is_up,
        status_code=status_code,
        response_ms=42,
        error=None,
    )
    save_check_result(conn, result)


def test_take_snapshot_empty_db(tmp_db):
    snap = take_snapshot(tmp_db)
    assert snap.entries == []
    assert isinstance(snap.taken_at, datetime)


def test_take_snapshot_includes_all_monitors(tmp_db):
    _make_monitor(tmp_db, name="m1", url="https://m1.example.com")
    _make_monitor(tmp_db, name="m2", url="https://m2.example.com")
    snap = take_snapshot(tmp_db)
    assert len(snap.entries) == 2


def test_take_snapshot_reflects_latest_status(tmp_db):
    m = _make_monitor(tmp_db)
    _insert_result(tmp_db, m.id, is_up=True)
    snap = take_snapshot(tmp_db)
    assert snap.entries[0].is_up is True


def test_snapshot_as_dict_shape(tmp_db):
    m = _make_monitor(tmp_db)
    _insert_result(tmp_db, m.id, is_up=False, status_code=500)
    snap = take_snapshot(tmp_db)
    d = snapshot_as_dict(snap)
    assert d["total"] == 1
    assert d["up"] == 0
    assert d["down"] == 1
    assert d["unknown"] == 0
    assert "taken_at" in d
    assert isinstance(d["monitors"], list)


def test_snapshot_as_dict_unknown(tmp_db):
    _make_monitor(tmp_db)  # no check result → unknown
    snap = take_snapshot(tmp_db)
    d = snapshot_as_dict(snap)
    assert d["unknown"] == 1
    assert d["up"] == 0
    assert d["down"] == 0


def test_snapshot_summary_line_format(tmp_db):
    _make_monitor(tmp_db)
    snap = take_snapshot(tmp_db)
    line = snapshot_summary_line(snap)
    assert "total=1" in line
    assert "up=0" in line
    assert "unknown=1" in line
