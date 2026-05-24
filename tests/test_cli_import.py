"""Tests for pulsemon.cli_import."""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import tempfile
from io import StringIO
from unittest.mock import patch

import pytest

from pulsemon.cli_import import add_import_parser, handle_import
from pulsemon.db import init_db
from pulsemon.monitors import list_monitors


@pytest.fixture()
def tmp_db_path(tmp_path):
    db = str(tmp_path / "test.db")
    conn = sqlite3.connect(db)
    init_db(conn)
    conn.close()
    return db


def _make_args(**kwargs) -> argparse.Namespace:
    defaults = {"file": "-", "db": "pulsemon.db", "dry_run": False, "format": "text"}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_add_import_parser_registers_command():
    root = argparse.ArgumentParser()
    sub = root.add_subparsers(dest="command")
    add_import_parser(sub)
    args = root.parse_args(["import", "monitors.json"])
    assert args.command == "import"


def test_add_import_parser_dry_run_flag():
    root = argparse.ArgumentParser()
    sub = root.add_subparsers(dest="command")
    add_import_parser(sub)
    args = root.parse_args(["import", "--dry-run", "monitors.json"])
    assert args.dry_run is True


def test_handle_import_from_stdin_creates_monitors(tmp_db_path, capsys):
    payload = json.dumps([
        {"name": "Alpha", "url": "https://alpha.example.com", "interval": 60, "timeout": 10},
        {"name": "Beta", "url": "https://beta.example.com", "interval": 120},
    ])
    args = _make_args(db=tmp_db_path)
    with patch("sys.stdin", StringIO(payload)):
        handle_import(args)

    conn = sqlite3.connect(tmp_db_path)
    monitors = list_monitors(conn)
    conn.close()
    assert len(monitors) == 2
    names = {m.name for m in monitors}
    assert names == {"Alpha", "Beta"}


def test_handle_import_dry_run_does_not_persist(tmp_db_path, capsys):
    payload = json.dumps([
        {"name": "Ghost", "url": "https://ghost.example.com", "interval": 60},
    ])
    args = _make_args(db=tmp_db_path, dry_run=True)
    with patch("sys.stdin", StringIO(payload)):
        handle_import(args)

    conn = sqlite3.connect(tmp_db_path)
    monitors = list_monitors(conn)
    conn.close()
    assert monitors == []


def test_handle_import_json_format_output(tmp_db_path, capsys):
    payload = json.dumps([
        {"name": "Omega", "url": "https://omega.example.com", "interval": 30},
    ])
    args = _make_args(db=tmp_db_path, format="json")
    with patch("sys.stdin", StringIO(payload)):
        handle_import(args)

    out = json.loads(capsys.readouterr().out)
    assert out["imported"] == 1
    assert out["skipped"] == 0


def test_handle_import_skips_invalid_entries(tmp_db_path, capsys):
    payload = json.dumps([
        {"name": "Good", "url": "https://good.example.com", "interval": 60},
        {"url": "https://noname.example.com"},  # missing 'name'
    ])
    args = _make_args(db=tmp_db_path)
    with patch("sys.stdin", StringIO(payload)):
        handle_import(args)

    out = capsys.readouterr().out
    assert "Imported 1 monitor(s), skipped 1." in out


def test_handle_import_file_not_found_exits(tmp_db_path):
    args = _make_args(db=tmp_db_path, file="/nonexistent/path.json")
    with pytest.raises(SystemExit) as exc_info:
        handle_import(args)
    assert exc_info.value.code == 1


def test_handle_import_invalid_json_exits(tmp_db_path):
    args = _make_args(db=tmp_db_path)
    with patch("sys.stdin", StringIO("not json at all")):
        with pytest.raises(SystemExit) as exc_info:
            handle_import(args)
    assert exc_info.value.code == 1
