"""Tests for pulsemon.cli_reset."""

from __future__ import annotations

import argparse
import io
import sqlite3
import tempfile
from pathlib import Path

import pytest

from pulsemon.cli_reset import add_reset_parser, handle_reset
from pulsemon.db import init_db


@pytest.fixture()
def tmp_db_path(tmp_path: Path) -> str:
    db_path = str(tmp_path / "test.db")
    conn = sqlite3.connect(db_path)
    init_db(conn)
    conn.close()
    return db_path


def _make_args(**kwargs) -> argparse.Namespace:
    defaults = {"db": "pulsemon.db", "monitor_id": None, "yes": True, "func": handle_reset}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _insert_result(db_path: str, monitor_id: int = 1) -> None:
    conn = sqlite3.connect(db_path)
    conn.execute(
        "INSERT INTO check_results (monitor_id, checked_at, status_code, is_up, latency_ms, error)"
        " VALUES (?, datetime('now'), 200, 1, 42.0, NULL)",
        (monitor_id,),
    )
    conn.commit()
    conn.close()


def _count_results(db_path: str, monitor_id: int | None = None) -> int:
    conn = sqlite3.connect(db_path)
    if monitor_id is not None:
        row = conn.execute(
            "SELECT COUNT(*) FROM check_results WHERE monitor_id = ?", (monitor_id,)
        ).fetchone()
    else:
        row = conn.execute("SELECT COUNT(*) FROM check_results").fetchone()
    conn.close()
    return row[0]


def test_add_reset_parser_registers_command():
    root = argparse.ArgumentParser()
    sub = root.add_subparsers()
    add_reset_parser(sub)
    args = root.parse_args(["reset", "--yes"])
    assert args.func is handle_reset


def test_handle_reset_deletes_all_results(tmp_db_path):
    _insert_result(tmp_db_path, monitor_id=1)
    _insert_result(tmp_db_path, monitor_id=2)
    assert _count_results(tmp_db_path) == 2

    out = io.StringIO()
    rc = handle_reset(_make_args(db=tmp_db_path, yes=True), out=out)

    assert rc == 0
    assert _count_results(tmp_db_path) == 0
    assert "all monitors" in out.getvalue()


def test_handle_reset_deletes_single_monitor(tmp_db_path):
    _insert_result(tmp_db_path, monitor_id=1)
    _insert_result(tmp_db_path, monitor_id=2)

    out = io.StringIO()
    rc = handle_reset(_make_args(db=tmp_db_path, monitor_id=1, yes=True), out=out)

    assert rc == 0
    assert _count_results(tmp_db_path, monitor_id=1) == 0
    assert _count_results(tmp_db_path, monitor_id=2) == 1
    assert "monitor 1" in out.getvalue()


def test_handle_reset_aborts_without_confirmation(tmp_db_path, monkeypatch):
    _insert_result(tmp_db_path, monitor_id=1)
    monkeypatch.setattr("builtins.input", lambda _: "no")

    out = io.StringIO()
    rc = handle_reset(_make_args(db=tmp_db_path, yes=False), out=out)

    assert rc == 1
    assert _count_results(tmp_db_path) == 1
    assert "Aborted" in out.getvalue()


def test_handle_reset_confirms_on_yes_input(tmp_db_path, monkeypatch):
    _insert_result(tmp_db_path, monitor_id=1)
    monkeypatch.setattr("builtins.input", lambda _: "yes")

    out = io.StringIO()
    rc = handle_reset(_make_args(db=tmp_db_path, yes=False), out=out)

    assert rc == 0
    assert _count_results(tmp_db_path) == 0
