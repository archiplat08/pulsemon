"""Tests for pulsemon.cli_pause."""
from __future__ import annotations

import argparse
import io
import json
import sqlite3
import tempfile
import os

import pytest

from pulsemon.db import init_db
from pulsemon.monitors import create_monitor
from pulsemon.models import Monitor
from pulsemon.cli_pause import add_pause_parser, handle_pause


@pytest.fixture()
def tmp_db_path(tmp_path):
    db = tmp_path / "test.db"
    conn = sqlite3.connect(str(db))
    init_db(conn)
    conn.close()
    return str(db)


def _make_args(**kwargs) -> argparse.Namespace:
    defaults = {
        "monitor_id": 1,
        "resume": False,
        "db": "pulsemon.db",
        "format": "text",
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _seed_monitor(db_path: str) -> int:
    from pulsemon.db import get_connection

    conn = get_connection(db_path)
    m = create_monitor(
        conn,
        Monitor(name="example", url="https://example.com", interval=60, timeout=5),
    )
    conn.close()
    return m.id


def test_add_pause_parser_registers_command():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command")
    add_pause_parser(sub)
    assert "pause" in {a.dest for a in sub._group_actions}  # noqa: SLF001


def test_add_pause_parser_has_resume_flag():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command")
    add_pause_parser(sub)
    ns = parser.parse_args(["pause", "3", "--resume"])
    assert ns.resume is True


def test_handle_pause_monitor_not_found(tmp_db_path):
    args = _make_args(monitor_id=999, db=tmp_db_path)
    rc = handle_pause(args)
    assert rc == 1


def test_handle_pause_text_output(tmp_db_path):
    mid = _seed_monitor(tmp_db_path)
    args = _make_args(monitor_id=mid, db=tmp_db_path, format="text")
    buf = io.StringIO()
    rc = handle_pause(args, out=buf)
    assert rc == 0
    assert "paused" in buf.getvalue()
    assert "example" in buf.getvalue()


def test_handle_pause_json_output(tmp_db_path):
    mid = _seed_monitor(tmp_db_path)
    args = _make_args(monitor_id=mid, db=tmp_db_path, format="json")
    buf = io.StringIO()
    rc = handle_pause(args, out=buf)
    assert rc == 0
    data = json.loads(buf.getvalue())
    assert data["action"] == "paused"
    assert data["id"] == mid


def test_handle_resume_text_output(tmp_db_path):
    mid = _seed_monitor(tmp_db_path)
    args = _make_args(monitor_id=mid, db=tmp_db_path, resume=True, format="text")
    buf = io.StringIO()
    rc = handle_pause(args, out=buf)
    assert rc == 0
    assert "resumed" in buf.getvalue()


def test_handle_pause_sets_paused_flag(tmp_db_path):
    from pulsemon.db import get_connection

    mid = _seed_monitor(tmp_db_path)
    args = _make_args(monitor_id=mid, db=tmp_db_path)
    handle_pause(args)
    conn = get_connection(tmp_db_path)
    row = conn.execute("SELECT paused FROM monitors WHERE id = ?", (mid,)).fetchone()
    conn.close()
    assert row[0] == 1
