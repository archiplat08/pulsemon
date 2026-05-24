"""Tests for pulsemon/cli_uptime.py."""
from __future__ import annotations

import argparse
import json
import sqlite3
from unittest.mock import patch

import pytest

from pulsemon.db import init_db
from pulsemon.cli_uptime import add_uptime_parser, handle_uptime


@pytest.fixture()
def tmp_db_path(tmp_path):
    db = tmp_path / "test.db"
    conn = sqlite3.connect(str(db))
    conn.row_factory = sqlite3.Row
    init_db(conn)
    conn.close()
    return str(db)


def _make_args(**kwargs):
    defaults = {"db": "pulsemon.db", "days": 30, "fmt": "text", "min_uptime": None}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_add_uptime_parser_registers_command():
    root = argparse.ArgumentParser()
    sub = root.add_subparsers(dest="cmd")
    add_uptime_parser(sub)
    args = root.parse_args(["uptime"])
    assert args.cmd == "uptime"


def test_add_uptime_parser_defaults():
    root = argparse.ArgumentParser()
    sub = root.add_subparsers(dest="cmd")
    add_uptime_parser(sub)
    args = root.parse_args(["uptime"])
    assert args.days == 30
    assert args.fmt == "text"
    assert args.min_uptime is None


def test_handle_uptime_no_monitors_text(tmp_db_path, capsys):
    args = _make_args(db=tmp_db_path)
    handle_uptime(args)
    out = capsys.readouterr().out
    assert "No monitors found" in out


def test_handle_uptime_no_monitors_json(tmp_db_path, capsys):
    args = _make_args(db=tmp_db_path, fmt="json")
    handle_uptime(args)
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data == []


def test_handle_uptime_text_shows_header(tmp_db_path, capsys):
    from pulsemon.db import get_connection
    from pulsemon.monitors import create_monitor
    from pulsemon.models import Monitor

    conn = get_connection(tmp_db_path)
    create_monitor(conn, Monitor(name="beta", url="https://beta.io", interval=60, timeout=5))
    conn.close()

    args = _make_args(db=tmp_db_path)
    handle_uptime(args)
    out = capsys.readouterr().out
    assert "beta" in out
    assert "N/A" in out


def test_handle_uptime_min_uptime_filters(tmp_db_path, capsys):
    from pulsemon.db import get_connection
    from pulsemon.monitors import create_monitor
    from pulsemon.models import Monitor

    conn = get_connection(tmp_db_path)
    m = create_monitor(conn, Monitor(name="gamma", url="https://gamma.io", interval=60, timeout=5))
    conn.execute(
        "INSERT INTO check_results (monitor_id, checked_at, is_up, status_code, response_ms, error)"
        " VALUES (?, datetime('now'), 1, 200, 10, NULL)",
        (m.id,),
    )
    conn.commit()
    conn.close()

    # 100% uptime, threshold 99 → should be filtered out
    args = _make_args(db=tmp_db_path, fmt="json", min_uptime=99.0)
    handle_uptime(args)
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data == []
