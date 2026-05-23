"""Tests for pulsemon.cli_purge."""

from __future__ import annotations

import argparse
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from pulsemon.cli_purge import add_purge_parser, handle_purge
from pulsemon.db import init_db


@pytest.fixture()
def tmp_db_path(tmp_path: Path) -> str:
    db_path = str(tmp_path / "test.db")
    init_db(db_path)
    return db_path


def _make_args(**kwargs) -> argparse.Namespace:
    defaults = {"days": 30, "dry_run": False, "db": "pulsemon.db"}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _insert_result(db_path: str, checked_at: datetime) -> None:
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        INSERT INTO check_results (monitor_id, status, status_code, response_time_ms, checked_at)
        VALUES (1, 'up', 200, 42, ?)
        """,
        (checked_at.isoformat(),),
    )
    conn.commit()
    conn.close()


def test_add_purge_parser_registers_command() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command")
    add_purge_parser(sub)
    args = parser.parse_args(["purge", "--days", "7"])
    assert args.command == "purge"
    assert args.days == 7


def test_handle_purge_deletes_old_rows(tmp_db_path: str, capsys) -> None:
    old = datetime.now(tz=timezone.utc) - timedelta(days=60)
    _insert_result(tmp_db_path, old)

    args = _make_args(db=tmp_db_path, days=30)
    handle_purge(args)

    out = capsys.readouterr().out
    assert "Deleted 1 result" in out

    conn = sqlite3.connect(tmp_db_path)
    count = conn.execute("SELECT COUNT(*) FROM check_results").fetchone()[0]
    conn.close()
    assert count == 0


def test_handle_purge_keeps_recent_rows(tmp_db_path: str, capsys) -> None:
    recent = datetime.now(tz=timezone.utc) - timedelta(days=5)
    _insert_result(tmp_db_path, recent)

    args = _make_args(db=tmp_db_path, days=30)
    handle_purge(args)

    out = capsys.readouterr().out
    assert "Deleted 0 result" in out

    conn = sqlite3.connect(tmp_db_path)
    count = conn.execute("SELECT COUNT(*) FROM check_results").fetchone()[0]
    conn.close()
    assert count == 1


def test_handle_purge_dry_run_does_not_delete(tmp_db_path: str, capsys) -> None:
    old = datetime.now(tz=timezone.utc) - timedelta(days=60)
    _insert_result(tmp_db_path, old)

    args = _make_args(db=tmp_db_path, days=30, dry_run=True)
    handle_purge(args)

    out = capsys.readouterr().out
    assert "[dry-run]" in out
    assert "1" in out

    conn = sqlite3.connect(tmp_db_path)
    count = conn.execute("SELECT COUNT(*) FROM check_results").fetchone()[0]
    conn.close()
    assert count == 1


def test_handle_purge_dry_run_zero(tmp_db_path: str, capsys) -> None:
    args = _make_args(db=tmp_db_path, days=30, dry_run=True)
    handle_purge(args)

    out = capsys.readouterr().out
    assert "[dry-run]" in out
    assert "0" in out
