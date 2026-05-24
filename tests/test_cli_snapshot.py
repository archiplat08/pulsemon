"""Tests for pulsemon.cli_snapshot."""
from __future__ import annotations

import argparse
import io
import json
import sqlite3
import tempfile
from pathlib import Path

import pytest

from pulsemon.db import init_db
from pulsemon.monitors import create_monitor
from pulsemon.cli_snapshot import add_snapshot_parser, handle_snapshot


@pytest.fixture()
def tmp_db_path(tmp_path):
    db = tmp_path / "test.db"
    conn = sqlite3.connect(str(db))
    conn.row_factory = sqlite3.Row
    init_db(conn)
    conn.close()
    return str(db)


def _make_args(db: str, fmt: str = "text", out=None):
    ns = argparse.Namespace(db=db, format=fmt, out=out)
    return ns


def test_add_snapshot_parser_registers_command():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command")
    add_snapshot_parser(sub)
    args = parser.parse_args(["snapshot"])
    assert args.command == "snapshot"


def test_handle_snapshot_empty_text(tmp_db_path):
    buf = io.StringIO()
    handle_snapshot(_make_args(tmp_db_path), out=buf)
    output = buf.getvalue()
    assert "Snapshot taken at" in output
    assert "No monitors found" in output


def test_handle_snapshot_empty_json(tmp_db_path):
    buf = io.StringIO()
    handle_snapshot(_make_args(tmp_db_path, fmt="json"), out=buf)
    data = json.loads(buf.getvalue())
    assert data["monitors"] == []
    assert "taken_at" in data


def test_handle_snapshot_lists_monitors(tmp_db_path):
    conn = sqlite3.connect(tmp_db_path)
    conn.row_factory = sqlite3.Row
    init_db(conn)
    create_monitor(conn, name="web", url="https://web.example.com", interval=60, timeout=5)
    conn.close()

    buf = io.StringIO()
    handle_snapshot(_make_args(tmp_db_path), out=buf)
    assert "web" in buf.getvalue()


def test_handle_snapshot_json_has_monitor_entry(tmp_db_path):
    conn = sqlite3.connect(tmp_db_path)
    conn.row_factory = sqlite3.Row
    init_db(conn)
    create_monitor(conn, name="api", url="https://api.example.com", interval=30, timeout=3)
    conn.close()

    buf = io.StringIO()
    handle_snapshot(_make_args(tmp_db_path, fmt="json"), out=buf)
    data = json.loads(buf.getvalue())
    assert len(data["monitors"]) == 1
    assert data["monitors"][0]["name"] == "api"


def test_handle_snapshot_writes_to_file(tmp_db_path, tmp_path):
    out_file = str(tmp_path / "snap.txt")
    handle_snapshot(_make_args(tmp_db_path, out=out_file))
    content = Path(out_file).read_text()
    assert "Snapshot taken at" in content
