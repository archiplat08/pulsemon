"""Unit tests for pulsemon.cli_labels."""
from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path
from unittest.mock import patch

import pytest

from pulsemon.cli_labels import add_labels_parser, handle_labels
from pulsemon.labels import set_label


@pytest.fixture()
def tmp_db_path(tmp_path: Path) -> str:
    db = str(tmp_path / "test.db")
    conn = sqlite3.connect(db)
    conn.execute(
        "CREATE TABLE monitors "
        "(id INTEGER PRIMARY KEY, name TEXT, url TEXT, interval INTEGER, "
        "timeout INTEGER, created_at TEXT)"
    )
    conn.execute(
        "INSERT INTO monitors VALUES (1, 'api', 'https://example.com', 60, 10, '2024-01-01')"
    )
    conn.commit()
    conn.close()
    return db


def _make_args(**kwargs) -> argparse.Namespace:
    defaults = {
        "monitor_id": 1,
        "set_kv": None,
        "remove_key": None,
        "format": "text",
        "db": ":memory:",
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_add_labels_parser_registers_command():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd")
    add_labels_parser(sub)
    args = p.parse_args(["label", "1"])
    assert args.monitor_id == 1


def test_handle_labels_list_empty(tmp_db_path, capsys):
    args = _make_args(monitor_id=1, db=tmp_db_path)
    handle_labels(args)
    out = capsys.readouterr().out
    assert "no labels" in out


def test_handle_labels_set_then_list(tmp_db_path, capsys):
    conn = sqlite3.connect(tmp_db_path)
    set_label(conn, 1, "env", "prod")
    conn.close()

    args = _make_args(monitor_id=1, db=tmp_db_path)
    handle_labels(args)
    out = capsys.readouterr().out
    assert "env" in out and "prod" in out


def test_handle_labels_set_via_cli(tmp_db_path, capsys):
    args = _make_args(monitor_id=1, set_kv="team=backend", db=tmp_db_path)
    handle_labels(args)
    out = capsys.readouterr().out
    assert "team" in out


def test_handle_labels_remove_via_cli(tmp_db_path, capsys):
    conn = sqlite3.connect(tmp_db_path)
    set_label(conn, 1, "env", "prod")
    conn.close()

    args = _make_args(monitor_id=1, remove_key="env", db=tmp_db_path)
    handle_labels(args)
    out = capsys.readouterr().out
    assert "removed" in out


def test_handle_labels_json_format(tmp_db_path, capsys):
    conn = sqlite3.connect(tmp_db_path)
    set_label(conn, 1, "region", "eu-west")
    conn.close()

    args = _make_args(monitor_id=1, format="json", db=tmp_db_path)
    handle_labels(args)
    data = json.loads(capsys.readouterr().out)
    assert data["region"] == "eu-west"


def test_handle_labels_monitor_not_found(tmp_db_path, capsys):
    args = _make_args(monitor_id=999, db=tmp_db_path)
    handle_labels(args)
    assert "not found" in capsys.readouterr().out


def test_handle_labels_set_invalid_format(tmp_db_path, capsys):
    args = _make_args(monitor_id=1, set_kv="badvalue", db=tmp_db_path)
    handle_labels(args)
    assert "KEY=VALUE" in capsys.readouterr().out
