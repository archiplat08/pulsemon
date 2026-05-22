"""Tests for pulsemon.cli_history."""

from __future__ import annotations

import argparse
import io
import json
import os
import tempfile

import pytest

from pulsemon.db import get_connection, init_db
from pulsemon.monitors import create_monitor
from pulsemon.models import Monitor, CheckResult
from pulsemon.checks import save_check_result
from pulsemon.cli_history import add_history_parser, handle_history


@pytest.fixture()
def tmp_db_path(tmp_path):
    db_file = tmp_path / "test.db"
    with get_connection(str(db_file)) as conn:
        init_db(conn)
    return str(db_file)


def _make_args(db_path: str, monitor_id: int, fmt: str = "text", limit: int = 20):
    ns = argparse.Namespace()
    ns.db = db_path
    ns.monitor_id = monitor_id
    ns.fmt = fmt
    ns.limit = limit
    return ns


def _seed_monitor(db_path: str):
    m = Monitor(name="Example", url="https://example.com", interval=60, timeout=5)
    with get_connection(db_path) as conn:
        return create_monitor(conn, m)


def _seed_result(db_path: str, monitor_id: int, status: str = "up"):
    r = CheckResult(
        monitor_id=monitor_id,
        status=status,
        status_code=200 if status == "up" else 500,
        response_time_ms=42.0,
        checked_at="2024-01-01T00:00:00",
        error=None,
    )
    with get_connection(db_path) as conn:
        save_check_result(conn, r)


def test_add_history_parser_registers_command():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_history_parser(sub)
    args = parser.parse_args(["history", "1"])
    assert args.monitor_id == 1
    assert args.fmt == "text"
    assert args.limit == 20


def test_handle_history_monitor_not_found(tmp_db_path):
    out = io.StringIO()
    args = _make_args(tmp_db_path, monitor_id=999)
    rc = handle_history(args, out=out)
    assert rc == 1


def test_handle_history_no_results_text(tmp_db_path):
    monitor = _seed_monitor(tmp_db_path)
    out = io.StringIO()
    args = _make_args(tmp_db_path, monitor_id=monitor.id)
    rc = handle_history(args, out=out)
    assert rc == 0
    text = out.getvalue()
    assert "Example" in text
    assert "No check results found." in text


def test_handle_history_text_with_results(tmp_db_path):
    monitor = _seed_monitor(tmp_db_path)
    _seed_result(tmp_db_path, monitor.id, status="up")
    out = io.StringIO()
    args = _make_args(tmp_db_path, monitor_id=monitor.id, fmt="text")
    rc = handle_history(args, out=out)
    assert rc == 0
    text = out.getvalue()
    assert "up" in text
    assert "100.0%" in text


def test_handle_history_json_with_results(tmp_db_path):
    monitor = _seed_monitor(tmp_db_path)
    _seed_result(tmp_db_path, monitor.id, status="up")
    _seed_result(tmp_db_path, monitor.id, status="down")
    out = io.StringIO()
    args = _make_args(tmp_db_path, monitor_id=monitor.id, fmt="json", limit=10)
    rc = handle_history(args, out=out)
    assert rc == 0
    data = json.loads(out.getvalue())
    assert data["monitor_id"] == monitor.id
    assert data["monitor_name"] == "Example"
    assert isinstance(data["uptime_percentage"], float)
    assert len(data["results"]) == 2
