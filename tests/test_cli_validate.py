"""Tests for pulsemon.cli_validate."""
from __future__ import annotations

import argparse
import json
import sqlite3
from io import StringIO
from unittest.mock import MagicMock, patch

import pytest

from pulsemon.cli_validate import add_validate_parser, handle_validate
from pulsemon.db import init_db
from pulsemon.models import CheckResult, Monitor
from pulsemon.monitors import create_monitor


@pytest.fixture()
def tmp_db_path(tmp_path):
    db_path = str(tmp_path / "test.db")
    conn = sqlite3.connect(db_path)
    init_db(conn)
    conn.close()
    return db_path


def _make_args(monitor_id: int, fmt: str = "text", db: str = "pulsemon.db"):
    ns = argparse.Namespace(monitor_id=monitor_id, fmt=fmt, db=db)
    return ns


def _seed_monitor(db_path: str) -> Monitor:
    conn = sqlite3.connect(db_path)
    init_db(conn)
    m = create_monitor(
        conn,
        name="Example",
        url="https://example.com",
        interval=60,
        timeout=5,
    )
    conn.close()
    return m


# ---------------------------------------------------------------------------
# Parser registration
# ---------------------------------------------------------------------------

def test_add_validate_parser_registers_command():
    root = argparse.ArgumentParser()
    sub = root.add_subparsers(dest="cmd")
    add_validate_parser(sub)
    args = root.parse_args(["validate", "1"])
    assert args.cmd == "validate"
    assert args.monitor_id == 1


def test_add_validate_parser_defaults():
    root = argparse.ArgumentParser()
    sub = root.add_subparsers(dest="cmd")
    add_validate_parser(sub)
    args = root.parse_args(["validate", "3"])
    assert args.fmt == "text"
    assert args.db == "pulsemon.db"


# ---------------------------------------------------------------------------
# handle_validate — monitor not found
# ---------------------------------------------------------------------------

def test_handle_validate_monitor_not_found(tmp_db_path):
    args = _make_args(monitor_id=999, db=tmp_db_path)
    rc = handle_validate(args, out=StringIO())
    assert rc == 1


# ---------------------------------------------------------------------------
# handle_validate — text format
# ---------------------------------------------------------------------------

def _up_result(monitor):
    return CheckResult(
        monitor_id=monitor.id,
        is_up=True,
        status_code=200,
        response_time_ms=42.5,
        error=None,
        checked_at="2024-01-01T00:00:00",
    )


def _down_result(monitor):
    return CheckResult(
        monitor_id=monitor.id,
        is_up=False,
        status_code=None,
        response_time_ms=None,
        error="timeout",
        checked_at="2024-01-01T00:00:00",
    )


def test_handle_validate_text_up(tmp_db_path):
    m = _seed_monitor(tmp_db_path)
    args = _make_args(monitor_id=m.id, fmt="text", db=tmp_db_path)
    out = StringIO()
    with patch("pulsemon.cli_validate.check_monitor", return_value=_up_result(m)):
        rc = handle_validate(args, out=out)
    assert rc == 0
    text = out.getvalue()
    assert "UP" in text
    assert "200" in text


def test_handle_validate_text_down(tmp_db_path):
    m = _seed_monitor(tmp_db_path)
    args = _make_args(monitor_id=m.id, fmt="text", db=tmp_db_path)
    out = StringIO()
    with patch("pulsemon.cli_validate.check_monitor", return_value=_down_result(m)):
        rc = handle_validate(args, out=out)
    assert rc == 2
    text = out.getvalue()
    assert "DOWN" in text
    assert "timeout" in text


# ---------------------------------------------------------------------------
# handle_validate — json format
# ---------------------------------------------------------------------------

def test_handle_validate_json_up(tmp_db_path):
    m = _seed_monitor(tmp_db_path)
    args = _make_args(monitor_id=m.id, fmt="json", db=tmp_db_path)
    out = StringIO()
    with patch("pulsemon.cli_validate.check_monitor", return_value=_up_result(m)):
        rc = handle_validate(args, out=out)
    assert rc == 0
    data = json.loads(out.getvalue())
    assert data["is_up"] is True
    assert data["status_code"] == 200
    assert data["monitor_id"] == m.id


def test_handle_validate_json_down(tmp_db_path):
    m = _seed_monitor(tmp_db_path)
    args = _make_args(monitor_id=m.id, fmt="json", db=tmp_db_path)
    out = StringIO()
    with patch("pulsemon.cli_validate.check_monitor", return_value=_down_result(m)):
        rc = handle_validate(args, out=out)
    assert rc == 2
    data = json.loads(out.getvalue())
    assert data["is_up"] is False
    assert data["error"] == "timeout"
