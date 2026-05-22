"""Tests for pulsemon/cli_status.py"""
import argparse
import io
import json
import sqlite3

import pytest

from pulsemon.db import init_db
from pulsemon.monitors import create_monitor
from pulsemon.checks import save_check_result
from pulsemon.models import Monitor, CheckResult
from pulsemon.cli_status import add_status_parser, handle_status
from datetime import datetime, timezone


@pytest.fixture
def tmp_db_path(tmp_path):
    db_file = tmp_path / "test.db"
    conn = sqlite3.connect(str(db_file))
    conn.row_factory = sqlite3.Row
    init_db(conn)
    m = Monitor(id=None, name="MyService", url="https://my.service", interval=60, timeout=5)
    mon = create_monitor(conn, m)
    r = CheckResult(
        id=None,
        monitor_id=mon.id,
        checked_at=datetime.now(timezone.utc).isoformat(),
        is_up=True,
        status_code=200,
        response_ms=30.0,
        error=None,
    )
    save_check_result(conn, r)
    conn.close()
    return str(db_file), mon.id


def _make_args(db, monitor_id=None, fmt="text"):
    args = argparse.Namespace(db=db, monitor_id=monitor_id, format=fmt)
    return args


def test_add_status_parser_registers_command():
    parser = argparse.ArgumentParser()
    subs = parser.add_subparsers()
    add_status_parser(subs)
    parsed = parser.parse_args(["status", "--format", "json"])
    assert parsed.format == "json"
    assert parsed.func is handle_status


def test_handle_status_text_stdout(tmp_db_path):
    db, _ = tmp_db_path
    out = io.StringIO()
    handle_status(_make_args(db, fmt="text"), out=out)
    text = out.getvalue()
    assert "MyService" in text
    assert "UP" in text


def test_handle_status_json_stdout(tmp_db_path):
    db, _ = tmp_db_path
    out = io.StringIO()
    handle_status(_make_args(db, fmt="json"), out=out)
    data = json.loads(out.getvalue())
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["name"] == "MyService"
    assert data[0]["is_up"] is True


def test_handle_status_single_monitor(tmp_db_path):
    db, monitor_id = tmp_db_path
    out = io.StringIO()
    handle_status(_make_args(db, monitor_id=monitor_id, fmt="json"), out=out)
    data = json.loads(out.getvalue())
    assert len(data) == 1
    assert data[0]["monitor_id"] == monitor_id


def test_handle_status_empty_db(tmp_path):
    db_file = tmp_path / "empty.db"
    conn = sqlite3.connect(str(db_file))
    init_db(conn)
    conn.close()
    out = io.StringIO()
    handle_status(_make_args(str(db_file), fmt="text"), out=out)
    assert "No monitors" in out.getvalue()
