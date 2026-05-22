"""Tests for pulsemon.cli_report."""
from __future__ import annotations

import argparse
import io
import json
import sqlite3
import tempfile
import os
from datetime import datetime, timezone

import pytest

from pulsemon.db import init_db
from pulsemon.monitors import create_monitor
from pulsemon.models import Monitor
from pulsemon.cli_report import add_report_parser, handle_report


@pytest.fixture()
def tmp_db_path():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    conn = sqlite3.connect(path)
    init_db(conn)
    conn.close()
    yield path
    os.unlink(path)


def _make_args(db: str, fmt: str = "text", limit: int = 50) -> argparse.Namespace:
    return argparse.Namespace(db=db, format=fmt, limit=limit)


def test_add_report_parser_registers_command():
    root = argparse.ArgumentParser()
    sub = root.add_subparsers(dest="command")
    add_report_parser(sub)
    args = root.parse_args(["report", "--db", "x.db"])
    assert args.command == "report"
    assert args.db == "x.db"
    assert args.format == "text"
    assert args.limit == 50


def test_handle_report_text_no_monitors(tmp_db_path):
    out = io.StringIO()
    handle_report(_make_args(tmp_db_path), out=out)
    assert "No monitors found" in out.getvalue()


def test_handle_report_text_with_monitor(tmp_db_path):
    conn = sqlite3.connect(tmp_db_path)
    m = Monitor(name="web", url="https://example.com", interval=60, timeout=5)
    create_monitor(conn, m)
    conn.close()

    out = io.StringIO()
    handle_report(_make_args(tmp_db_path), out=out)
    text = out.getvalue()
    assert "web" in text
    assert "https://example.com" in text
    assert "UNKNOWN" in text


def test_handle_report_json_empty(tmp_db_path):
    out = io.StringIO()
    handle_report(_make_args(tmp_db_path, fmt="json"), out=out)
    data = json.loads(out.getvalue())
    assert data == []


def test_handle_report_json_with_monitor(tmp_db_path):
    conn = sqlite3.connect(tmp_db_path)
    m = Monitor(name="api", url="https://api.example.com", interval=30, timeout=10)
    create_monitor(conn, m)
    conn.close()

    out = io.StringIO()
    handle_report(_make_args(tmp_db_path, fmt="json"), out=out)
    data = json.loads(out.getvalue())
    assert len(data) == 1
    assert data[0]["monitor"]["name"] == "api"
    assert "uptime_percentage" in data[0]
    assert "total_checks" in data[0]
