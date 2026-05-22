"""Tests for pulsemon.cli_notify sub-command."""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from pulsemon.cli_notify import add_notify_parser, handle_notify
from pulsemon.db import init_db
from pulsemon.monitors import create_monitor
from pulsemon.checks import save_check_result
from pulsemon.models import Monitor, CheckResult


@pytest.fixture()
def tmp_db_path(tmp_path: Path) -> str:
    db_file = tmp_path / "test.db"
    conn = sqlite3.connect(str(db_file))
    init_db(conn)
    conn.close()
    return str(db_file)


def _make_args(**kwargs) -> SimpleNamespace:
    defaults = {"config": "nonexistent.toml", "db": "", "as_json": False, "monitor_id": 1}
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def test_add_notify_parser_registers_command():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command")
    add_notify_parser(sub)
    ns = parser.parse_args(["notify", "42"])
    assert ns.monitor_id == 42


def test_handle_notify_monitor_not_found(tmp_db_path):
    args = _make_args(db=tmp_db_path, monitor_id=999)
    with patch("pulsemon.cli_notify.load_config"):
        rc = handle_notify(args)
    assert rc == 1


def test_handle_notify_no_check_results(tmp_db_path):
    conn = sqlite3.connect(tmp_db_path)
    m = Monitor(name="ping", url="https://ping.example.com", interval=60, timeout=5)
    created = create_monitor(conn, m)
    conn.close()

    args = _make_args(db=tmp_db_path, monitor_id=created.id)
    with patch("pulsemon.cli_notify.load_config"):
        rc = handle_notify(args)
    assert rc == 1


def test_handle_notify_text_output(tmp_db_path, capsys):
    conn = sqlite3.connect(tmp_db_path)
    m = Monitor(name="ping", url="https://ping.example.com", interval=60, timeout=5)
    created = create_monitor(conn, m)
    result = CheckResult(monitor_id=created.id, is_up=True, status_code=200, response_time=0.1, checked_at="2024-01-01T00:00:00")
    save_check_result(conn, result)
    conn.close()

    args = _make_args(db=tmp_db_path, monitor_id=created.id)
    with patch("pulsemon.cli_notify.load_config"), patch("pulsemon.cli_notify.notify", return_value={"webhook": False, "email": False}):
        rc = handle_notify(args)

    assert rc == 0
    captured = capsys.readouterr()
    assert "ping" in captured.out


def test_handle_notify_json_output(tmp_db_path, capsys):
    conn = sqlite3.connect(tmp_db_path)
    m = Monitor(name="ping", url="https://ping.example.com", interval=60, timeout=5)
    created = create_monitor(conn, m)
    result = CheckResult(monitor_id=created.id, is_up=False, status_code=503, response_time=0.2, checked_at="2024-01-01T00:00:00")
    save_check_result(conn, result)
    conn.close()

    args = _make_args(db=tmp_db_path, monitor_id=created.id, as_json=True)
    with patch("pulsemon.cli_notify.load_config"), patch("pulsemon.cli_notify.notify", return_value={"webhook": True, "email": False}):
        rc = handle_notify(args)

    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert data["monitor_id"] == created.id
    assert data["webhook"] is True
    assert data["email"] is False
