"""Tests for pulsemon.cli_ping."""
from __future__ import annotations

import argparse
import io
import json
from unittest.mock import MagicMock, patch

import pytest

from pulsemon.cli_ping import add_ping_parser, handle_ping
from pulsemon.db import init_db
from pulsemon.models import CheckResult, Monitor
from pulsemon.monitors import create_monitor


@pytest.fixture()
def tmp_db_path(tmp_path):
    db_file = tmp_path / "test.db"
    import sqlite3
    conn = sqlite3.connect(str(db_file))
    init_db(conn)
    conn.close()
    return str(db_file)


def _make_args(**kwargs):
    defaults = {
        "monitor_id": 1,
        "db": ":memory:",
        "save": False,
        "format": "text",
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


_MONITOR = Monitor(
    id=1,
    name="example",
    url="https://example.com",
    interval=60,
    timeout=5,
    created_at="2024-01-01T00:00:00",
)

_RESULT_UP = CheckResult(
    id=None,
    monitor_id=1,
    status="up",
    response_time_ms=42.0,
    status_code=200,
    error=None,
    checked_at="2024-01-01T00:01:00",
)

_RESULT_DOWN = CheckResult(
    id=None,
    monitor_id=1,
    status="down",
    response_time_ms=None,
    status_code=None,
    error="connection refused",
    checked_at="2024-01-01T00:01:00",
)


def test_add_ping_parser_registers_command():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command")
    add_ping_parser(sub)
    args = parser.parse_args(["ping", "7"])
    assert args.monitor_id == 7


def test_add_ping_parser_defaults():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command")
    add_ping_parser(sub)
    args = parser.parse_args(["ping", "3"])
    assert args.save is False
    assert args.format == "text"
    assert args.db == "pulsemon.db"


def test_handle_ping_monitor_not_found(tmp_db_path):
    args = _make_args(monitor_id=999, db=tmp_db_path)
    rc = handle_ping(args)
    assert rc == 2


def test_handle_ping_text_up(tmp_db_path):
    with patch("pulsemon.cli_ping.get_monitor", return_value=_MONITOR), \
         patch("pulsemon.cli_ping.check_monitor", return_value=_RESULT_UP):
        out = io.StringIO()
        args = _make_args(db=tmp_db_path, format="text")
        rc = handle_ping(args, out=out)
    assert rc == 0
    assert "UP" in out.getvalue()
    assert "example" in out.getvalue()


def test_handle_ping_text_down(tmp_db_path):
    with patch("pulsemon.cli_ping.get_monitor", return_value=_MONITOR), \
         patch("pulsemon.cli_ping.check_monitor", return_value=_RESULT_DOWN):
        out = io.StringIO()
        args = _make_args(db=tmp_db_path, format="text")
        rc = handle_ping(args, out=out)
    assert rc == 1
    assert "DOWN" in out.getvalue()
    assert "connection refused" in out.getvalue()


def test_handle_ping_json_format(tmp_db_path):
    with patch("pulsemon.cli_ping.get_monitor", return_value=_MONITOR), \
         patch("pulsemon.cli_ping.check_monitor", return_value=_RESULT_UP):
        out = io.StringIO()
        args = _make_args(db=tmp_db_path, format="json")
        rc = handle_ping(args, out=out)
    assert rc == 0
    data = json.loads(out.getvalue())
    assert data["status"] == "up"
    assert data["monitor_id"] == 1
    assert data["response_time_ms"] == 42.0


def test_handle_ping_save_calls_save_check_result(tmp_db_path):
    with patch("pulsemon.cli_ping.get_monitor", return_value=_MONITOR), \
         patch("pulsemon.cli_ping.check_monitor", return_value=_RESULT_UP), \
         patch("pulsemon.cli_ping.save_check_result") as mock_save:
        args = _make_args(db=tmp_db_path, save=True)
        handle_ping(args, out=io.StringIO())
    mock_save.assert_called_once()


def test_handle_ping_no_save_skips_db_write(tmp_db_path):
    with patch("pulsemon.cli_ping.get_monitor", return_value=_MONITOR), \
         patch("pulsemon.cli_ping.check_monitor", return_value=_RESULT_UP), \
         patch("pulsemon.cli_ping.save_check_result") as mock_save:
        args = _make_args(db=tmp_db_path, save=False)
        handle_ping(args, out=io.StringIO())
    mock_save.assert_not_called()
