"""Tests for pulsemon.cli_check."""
from __future__ import annotations

import argparse
import json
from unittest.mock import MagicMock, patch

import pytest

from pulsemon.cli_check import add_check_parser, handle_check
from pulsemon.db import get_connection, init_db
from pulsemon.models import CheckResult, Monitor
from pulsemon.monitors import create_monitor


@pytest.fixture()
def tmp_db_path(tmp_path):
    path = str(tmp_path / "test.db")
    conn = get_connection(path)
    init_db(conn)
    conn.close()
    return path


def _make_args(**kwargs):
    defaults = {"monitor_id": 1, "fmt": "text", "save": False}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _make_result(status="up", response_time_ms=42.0, status_code=200, error=None):
    return CheckResult(
        id=None,
        monitor_id=1,
        status=status,
        response_time_ms=response_time_ms,
        status_code=status_code,
        error=error,
        checked_at="2024-01-01T00:00:00",
    )


def test_add_check_parser_registers_command():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command")
    add_check_parser(sub)
    parsed = parser.parse_args(["check", "3"])
    assert parsed.monitor_id == 3
    assert parsed.fmt == "text"
    assert parsed.save is False


def test_handle_check_monitor_not_found(tmp_db_path, capsys):
    args = _make_args(monitor_id=999)
    with pytest.raises(SystemExit) as exc:
        handle_check(args, tmp_db_path)
    assert exc.value.code == 1
    captured = capsys.readouterr()
    assert "not found" in captured.err


def test_handle_check_text_output(tmp_db_path, capsys):
    conn = get_connection(tmp_db_path)
    m = Monitor(id=None, name="Test", url="http://example.com", interval=60, timeout=5)
    create_monitor(conn, m)
    conn.close()

    result = _make_result()
    with patch("pulsemon.cli_check.check_monitor", return_value=result):
        handle_check(_make_args(monitor_id=1, fmt="text", save=False), tmp_db_path)

    out = capsys.readouterr().out
    assert "UP" in out
    assert "42.0 ms" in out


def test_handle_check_json_output(tmp_db_path, capsys):
    conn = get_connection(tmp_db_path)
    m = Monitor(id=None, name="Test", url="http://example.com", interval=60, timeout=5)
    create_monitor(conn, m)
    conn.close()

    result = _make_result()
    with patch("pulsemon.cli_check.check_monitor", return_value=result):
        handle_check(_make_args(monitor_id=1, fmt="json", save=False), tmp_db_path)

    data = json.loads(capsys.readouterr().out)
    assert data["status"] == "up"
    assert data["response_time_ms"] == 42.0


def test_handle_check_save_persists_result(tmp_db_path):
    conn = get_connection(tmp_db_path)
    m = Monitor(id=None, name="Test", url="http://example.com", interval=60, timeout=5)
    create_monitor(conn, m)
    conn.close()

    result = _make_result()
    with patch("pulsemon.cli_check.check_monitor", return_value=result):
        with patch("pulsemon.cli_check.save_check_result") as mock_save:
            handle_check(_make_args(monitor_id=1, save=True), tmp_db_path)
            mock_save.assert_called_once()


def test_handle_check_down_shows_error(tmp_db_path, capsys):
    conn = get_connection(tmp_db_path)
    m = Monitor(id=None, name="Test", url="http://example.com", interval=60, timeout=5)
    create_monitor(conn, m)
    conn.close()

    result = _make_result(status="down", response_time_ms=None, status_code=None, error="timeout")
    with patch("pulsemon.cli_check.check_monitor", return_value=result):
        handle_check(_make_args(monitor_id=1, fmt="text"), tmp_db_path)

    out = capsys.readouterr().out
    assert "DOWN" in out
    assert "timeout" in out
