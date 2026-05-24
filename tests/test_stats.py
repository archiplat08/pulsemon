"""Tests for pulsemon/stats.py and pulsemon/cli_stats.py."""
from __future__ import annotations

import json
import sqlite3
from types import SimpleNamespace

import pytest

from pulsemon.db import init_db
from pulsemon.stats import MonitorStats, get_monitor_stats, stats_as_dict
from pulsemon.cli_stats import add_stats_parser, handle_stats


@pytest.fixture()
def tmp_db(tmp_path):
    db_file = tmp_path / "test.db"
    conn = sqlite3.connect(str(db_file))
    conn.row_factory = sqlite3.Row
    init_db(conn)
    yield conn
    conn.close()


def _make_monitor(conn: sqlite3.Connection, name: str = "m1") -> int:
    cur = conn.execute(
        "INSERT INTO monitors (name, url, interval, timeout, created_at) VALUES (?,?,?,?,?)",
        (name, "http://example.com", 60, 5, "2024-01-01T00:00:00"),
    )
    conn.commit()
    return cur.lastrowid


def _insert_result(
    conn: sqlite3.Connection,
    monitor_id: int,
    is_up: bool,
    response_ms: float,
    checked_at: str = "2024-01-01T00:00:00",
) -> None:
    conn.execute(
        "INSERT INTO check_results (monitor_id, is_up, status_code, response_ms, checked_at)"
        " VALUES (?,?,?,?,?)",
        (monitor_id, int(is_up), 200 if is_up else 0, response_ms, checked_at),
    )
    conn.commit()


# --- unit tests for stats.py ---

def test_get_monitor_stats_no_results(tmp_db):
    mid = _make_monitor(tmp_db)
    s = get_monitor_stats(tmp_db, mid)
    assert s.sample_size == 0
    assert s.min_ms == 0.0
    assert s.error_rate == 0.0


def test_get_monitor_stats_all_up(tmp_db):
    mid = _make_monitor(tmp_db)
    for ms in [100.0, 200.0, 300.0, 400.0, 500.0]:
        _insert_result(tmp_db, mid, True, ms)
    s = get_monitor_stats(tmp_db, mid)
    assert s.sample_size == 5
    assert s.min_ms == 100.0
    assert s.max_ms == 500.0
    assert s.avg_ms == pytest.approx(300.0)
    assert s.error_rate == 0.0


def test_get_monitor_stats_error_rate(tmp_db):
    mid = _make_monitor(tmp_db)
    _insert_result(tmp_db, mid, True, 100.0)
    _insert_result(tmp_db, mid, False, 0.0)
    s = get_monitor_stats(tmp_db, mid)
    assert s.error_rate == pytest.approx(0.5)


def test_get_monitor_stats_respects_limit(tmp_db):
    mid = _make_monitor(tmp_db)
    for ms in range(1, 21):  # 20 results
        _insert_result(tmp_db, mid, True, float(ms))
    s = get_monitor_stats(tmp_db, mid, limit=5)
    assert s.sample_size == 5


def test_stats_as_dict_keys(tmp_db):
    mid = _make_monitor(tmp_db)
    _insert_result(tmp_db, mid, True, 250.0)
    s = get_monitor_stats(tmp_db, mid)
    d = stats_as_dict(s)
    for key in ("monitor_id", "sample_size", "min_ms", "max_ms", "avg_ms", "p95_ms", "p99_ms", "error_rate"):
        assert key in d


# --- unit tests for cli_stats.py ---

def test_add_stats_parser_registers_command():
    import argparse
    root = argparse.ArgumentParser()
    sub = root.add_subparsers(dest="cmd")
    add_stats_parser(sub)
    args = root.parse_args(["stats", "42"])
    assert args.cmd == "stats"
    assert args.monitor_id == 42
    assert args.limit == 100
    assert args.fmt == "text"


def test_handle_stats_monitor_not_found(tmp_db, tmp_path, capsys):
    db_file = tmp_path / "x.db"
    import shutil
    # write the tmp_db file path isn't available directly; use in-memory approach via monkeypatching
    args = SimpleNamespace(monitor_id=999, limit=100, fmt="text", db=None)
    # patch get_connection to return our tmp_db
    import pulsemon.cli_stats as cs
    original = cs.get_connection
    cs.get_connection = lambda _: tmp_db
    try:
        handle_stats(args)
    finally:
        cs.get_connection = original
    out = capsys.readouterr().out
    assert "not found" in out


def test_handle_stats_json_output(tmp_db, capsys):
    mid = _make_monitor(tmp_db)
    _insert_result(tmp_db, mid, True, 123.0)
    args = SimpleNamespace(monitor_id=mid, limit=100, fmt="json", db=None)
    import pulsemon.cli_stats as cs
    original = cs.get_connection
    cs.get_connection = lambda _: tmp_db
    try:
        handle_stats(args)
    finally:
        cs.get_connection = original
    data = json.loads(capsys.readouterr().out)
    assert data["monitor_id"] == mid
    assert data["sample_size"] == 1
