"""Tests for pulsemon.cli_export."""

from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from pulsemon.cli_export import add_export_parser, handle_export
from pulsemon.db import init_db


@pytest.fixture()
def tmp_db_path(tmp_path):
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    init_db(conn)
    conn.execute(
        """
        INSERT INTO check_results (monitor_id, checked_at, status, response_time_ms, status_code, error)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (7, datetime.now(timezone.utc).isoformat(), "up", 80, 200, None),
    )
    conn.commit()
    conn.close()
    return db_path


def _make_args(**kwargs) -> argparse.Namespace:
    defaults = {
        "monitor_id": 7,
        "fmt": "json",
        "limit": 1000,
        "output": None,
        "db": ":memory:",
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_add_export_parser_registers_command():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_export_parser(sub)
    args = parser.parse_args(["export", "42", "--format", "csv", "--limit", "50"])
    assert args.monitor_id == 42
    assert args.fmt == "csv"
    assert args.limit == 50


def test_handle_export_json_stdout(tmp_db_path, capsys):
    args = _make_args(monitor_id=7, fmt="json", db=str(tmp_db_path))
    rc = handle_export(args)
    assert rc == 0
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert isinstance(data, list)
    assert data[0]["status"] == "up"


def test_handle_export_csv_stdout(tmp_db_path, capsys):
    args = _make_args(monitor_id=7, fmt="csv", db=str(tmp_db_path))
    rc = handle_export(args)
    assert rc == 0
    captured = capsys.readouterr()
    assert "status" in captured.out
    assert "up" in captured.out


def test_handle_export_writes_file(tmp_db_path, tmp_path):
    out_file = tmp_path / "results.json"
    args = _make_args(monitor_id=7, fmt="json", db=str(tmp_db_path), output=out_file)
    rc = handle_export(args)
    assert rc == 0
    assert out_file.exists()
    data = json.loads(out_file.read_text())
    assert len(data) == 1


def test_handle_export_invalid_format_returns_error(tmp_db_path, capsys):
    args = _make_args(monitor_id=7, db=str(tmp_db_path))
    # Bypass argparse choices validation by patching export_monitor_history
    with patch("pulsemon.cli_export.export_monitor_history", side_effect=ValueError("bad fmt")):
        rc = handle_export(args)
    assert rc == 1
    captured = capsys.readouterr()
    assert "error" in captured.err
