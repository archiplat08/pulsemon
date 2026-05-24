"""Tests for pulsemon/cli_copy.py."""
from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path

import pytest

from pulsemon.db import init_db
from pulsemon.monitors import create_monitor
from pulsemon.models import Monitor
from pulsemon.cli_copy import add_copy_parser, handle_copy


@pytest.fixture()
def tmp_db_path(tmp_path: Path) -> str:
    db_path = str(tmp_path / "test.db")
    conn = sqlite3.connect(db_path)
    init_db(conn)
    conn.close()
    return db_path


def _make_args(**kwargs) -> argparse.Namespace:
    defaults = {
        "monitor_id": 1,
        "new_name": "Clone",
        "new_url": None,
        "db": "pulsemon.db",
        "json_fmt": False,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _seed_monitor(db_path: str) -> Monitor:
    conn = sqlite3.connect(db_path)
    init_db(conn)
    m = create_monitor(
        conn,
        Monitor(id=None, name="Original", url="https://example.com", interval=60, timeout=10, tags="web"),
    )
    conn.close()
    return m


def test_add_copy_parser_registers_command() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd")
    add_copy_parser(sub)
    args = parser.parse_args(["copy", "1", "MyClone"])
    assert args.cmd == "copy"
    assert args.monitor_id == 1
    assert args.new_name == "MyClone"


def test_handle_copy_creates_new_monitor(tmp_db_path: str, capsys) -> None:
    source = _seed_monitor(tmp_db_path)
    args = _make_args(monitor_id=source.id, new_name="ClonedMonitor", db=tmp_db_path)
    handle_copy(args)
    out = capsys.readouterr().out
    assert "ClonedMonitor" in out
    assert str(source.id) in out


def test_handle_copy_inherits_url(tmp_db_path: str, capsys) -> None:
    source = _seed_monitor(tmp_db_path)
    args = _make_args(monitor_id=source.id, new_name="Clone2", db=tmp_db_path)
    handle_copy(args)
    out = capsys.readouterr().out
    assert "https://example.com" in out


def test_handle_copy_override_url(tmp_db_path: str, capsys) -> None:
    source = _seed_monitor(tmp_db_path)
    args = _make_args(
        monitor_id=source.id,
        new_name="CloneNew",
        new_url="https://other.example.com",
        db=tmp_db_path,
    )
    handle_copy(args)
    out = capsys.readouterr().out
    assert "https://other.example.com" in out


def test_handle_copy_monitor_not_found(tmp_db_path: str, capsys) -> None:
    args = _make_args(monitor_id=999, new_name="Ghost", db=tmp_db_path)
    handle_copy(args)
    out = capsys.readouterr().out
    assert "not found" in out


def test_handle_copy_json_output(tmp_db_path: str, capsys) -> None:
    source = _seed_monitor(tmp_db_path)
    args = _make_args(monitor_id=source.id, new_name="JsonClone", db=tmp_db_path, json_fmt=True)
    handle_copy(args)
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["name"] == "JsonClone"
    assert data["source_id"] == source.id
    assert "new_id" in data
