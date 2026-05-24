"""Tests for pulsemon.cli_rename."""
from __future__ import annotations

import argparse
import io
import json
import sqlite3

import pytest

from pulsemon.cli_rename import add_rename_parser, handle_rename
from pulsemon.db import init_db
from pulsemon.monitors import create_monitor
from pulsemon.models import Monitor


@pytest.fixture()
def tmp_db_path(tmp_path):
    db_path = str(tmp_path / "test.db")
    conn = sqlite3.connect(db_path)
    init_db(conn)
    conn.close()
    return db_path


def _make_args(**kwargs) -> argparse.Namespace:
    defaults = {"monitor_id": 1, "new_name": "New Name", "db": "", "json_output": False}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _seed_monitor(db_path: str, name: str = "Original") -> int:
    conn = sqlite3.connect(db_path)
    m = Monitor(name=name, url="https://example.com", interval=60, timeout=10)
    created = create_monitor(conn, m)
    conn.close()
    return created.id


def test_add_rename_parser_registers_command():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command")
    add_rename_parser(sub)
    args = parser.parse_args(["rename", "3", "My New Name"])
    assert args.command == "rename"
    assert args.monitor_id == 3
    assert args.new_name == "My New Name"


def test_handle_rename_success_text(tmp_db_path):
    mid = _seed_monitor(tmp_db_path, "OldName")
    out, err = io.StringIO(), io.StringIO()
    args = _make_args(monitor_id=mid, new_name="BrandNew", db=tmp_db_path)
    rc = handle_rename(args, out=out, err=err)
    assert rc == 0
    output = out.getvalue()
    assert "OldName" in output
    assert "BrandNew" in output


def test_handle_rename_success_json(tmp_db_path):
    mid = _seed_monitor(tmp_db_path, "Alpha")
    out, err = io.StringIO(), io.StringIO()
    args = _make_args(monitor_id=mid, new_name="Beta", db=tmp_db_path, json_output=True)
    rc = handle_rename(args, out=out, err=err)
    assert rc == 0
    data = json.loads(out.getvalue())
    assert data["old_name"] == "Alpha"
    assert data["new_name"] == "Beta"
    assert data["id"] == mid


def test_handle_rename_monitor_not_found(tmp_db_path):
    out, err = io.StringIO(), io.StringIO()
    args = _make_args(monitor_id=9999, new_name="Anything", db=tmp_db_path)
    rc = handle_rename(args, out=out, err=err)
    assert rc == 1
    assert "not found" in err.getvalue()


def test_handle_rename_empty_name_rejected(tmp_db_path):
    mid = _seed_monitor(tmp_db_path)
    out, err = io.StringIO(), io.StringIO()
    args = _make_args(monitor_id=mid, new_name="   ", db=tmp_db_path)
    rc = handle_rename(args, out=out, err=err)
    assert rc == 1
    assert "empty" in err.getvalue()


def test_handle_rename_persists_to_db(tmp_db_path):
    mid = _seed_monitor(tmp_db_path, "BeforeRename")
    args = _make_args(monitor_id=mid, new_name="AfterRename", db=tmp_db_path)
    handle_rename(args, out=io.StringIO(), err=io.StringIO())
    conn = sqlite3.connect(tmp_db_path)
    row = conn.execute("SELECT name FROM monitors WHERE id = ?", (mid,)).fetchone()
    conn.close()
    assert row[0] == "AfterRename"
