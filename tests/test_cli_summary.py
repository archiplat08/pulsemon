"""Tests for pulsemon.cli_summary."""
from __future__ import annotations

import argparse
import json
import sqlite3
from io import StringIO
from pathlib import Path

import pytest

from pulsemon.cli_summary import add_summary_parser, handle_summary
from pulsemon.db import init_db
from pulsemon.monitors import create_monitor
from pulsemon.models import Monitor


@pytest.fixture()
def tmp_db_path(tmp_path: Path) -> str:
    db_path = str(tmp_path / "test.db")
    conn = sqlite3.connect(db_path)
    init_db(conn)
    conn.close()
    return db_path


def _make_args(db: str, fmt: str = "text", only_down: bool = False) -> argparse.Namespace:
    return argparse.Namespace(db=db, format=fmt, only_down=only_down)


def _seed_monitor(db_path: str, name: str = "example") -> Monitor:
    conn = sqlite3.connect(db_path)
    m = create_monitor(conn, name=name, url="https://example.com", interval=60, timeout=10)
    conn.close()
    return m


def test_add_summary_parser_registers_command():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command")
    add_summary_parser(sub)
    args = parser.parse_args(["summary"])
    assert args.command == "summary"


def test_add_summary_parser_defaults():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command")
    add_summary_parser(sub)
    args = parser.parse_args(["summary"])
    assert args.db == "pulsemon.db"
    assert args.format == "text"
    assert args.only_down is False


def test_handle_summary_no_monitors_text(tmp_db_path: str):
    out = StringIO()
    code = handle_summary(_make_args(tmp_db_path), out=out)
    assert code == 0
    assert "No monitors found" in out.getvalue()


def test_handle_summary_no_monitors_json(tmp_db_path: str):
    out = StringIO()
    code = handle_summary(_make_args(tmp_db_path, fmt="json"), out=out)
    assert code == 0
    data = json.loads(out.getvalue())
    assert data == []


def test_handle_summary_with_monitor_text(tmp_db_path: str):
    _seed_monitor(tmp_db_path, name="my-site")
    out = StringIO()
    code = handle_summary(_make_args(tmp_db_path), out=out)
    assert code == 0
    output = out.getvalue()
    assert "my-site" in output
    assert "UNKNOWN" in output


def test_handle_summary_json_shape(tmp_db_path: str):
    _seed_monitor(tmp_db_path, name="api")
    out = StringIO()
    handle_summary(_make_args(tmp_db_path, fmt="json"), out=out)
    data = json.loads(out.getvalue())
    assert len(data) == 1
    assert "name" in data[0]
    assert "status" in data[0]


def test_handle_summary_only_down_flag_filters(tmp_db_path: str):
    _seed_monitor(tmp_db_path, name="healthy")
    out = StringIO()
    code = handle_summary(_make_args(tmp_db_path, only_down=True), out=out)
    # No down monitors → empty output (no table rows beyond header)
    assert code == 0
    assert "healthy" not in out.getvalue()
