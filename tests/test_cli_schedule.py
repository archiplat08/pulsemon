"""Tests for pulsemon/cli_schedule.py."""
from __future__ import annotations

import argparse
import io
import json
import sqlite3
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest

from pulsemon.db import init_db
from pulsemon.monitors import create_monitor
from pulsemon.models import Monitor
from pulsemon.cli_schedule import add_schedule_parser, handle_schedule


@pytest.fixture()
def tmp_db_path(tmp_path: Path) -> str:
    db_path = str(tmp_path / "test.db")
    conn = sqlite3.connect(db_path)
    init_db(conn)
    conn.close()
    return db_path


def _make_args(db: str, fmt: str = "text") -> argparse.Namespace:
    return argparse.Namespace(db=db, format=fmt)


def _make_monitor(db: str, name: str = "alpha", url: str = "http://example.com", interval: int = 60) -> Monitor:
    conn = sqlite3.connect(db)
    m = create_monitor(conn, name=name, url=url, interval=interval)
    conn.close()
    return m


def test_add_schedule_parser_registers_command():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd")
    add_schedule_parser(sub)
    ns = parser.parse_args(["schedule", "--db", "x.db"])
    assert ns.db == "x.db"


def test_handle_schedule_no_monitors_text(tmp_db_path):
    out = io.StringIO()
    handle_schedule(_make_args(tmp_db_path, "text"), out=out)
    assert "No monitors" in out.getvalue()


def test_handle_schedule_no_monitors_json(tmp_db_path):
    out = io.StringIO()
    handle_schedule(_make_args(tmp_db_path, "json"), out=out)
    data = json.loads(out.getvalue())
    assert data == []


def test_handle_schedule_with_monitor_text(tmp_db_path):
    _make_monitor(tmp_db_path)
    out = io.StringIO()
    handle_schedule(_make_args(tmp_db_path, "text"), out=out)
    text = out.getvalue()
    assert "alpha" in text
    assert "60" in text


def test_handle_schedule_with_monitor_json(tmp_db_path):
    m = _make_monitor(tmp_db_path, name="beta", interval=120)
    out = io.StringIO()
    handle_schedule(_make_args(tmp_db_path, "json"), out=out)
    data = json.loads(out.getvalue())
    assert len(data) == 1
    row = data[0]
    assert row["name"] == "beta"
    assert row["interval"] == 120
    assert "next_check" in row
    assert "seconds_until" in row
    assert row["seconds_until"] == 0  # no prior check → immediate


def test_handle_schedule_seconds_until_after_recent_check(tmp_db_path):
    """After a very recent check, seconds_until should be > 0."""
    import sqlite3 as _sqlite3

    m = _make_monitor(tmp_db_path, interval=300)
    now = datetime.now(tz=timezone.utc)
    conn = _sqlite3.connect(tmp_db_path)
    conn.execute(
        "INSERT INTO check_results (monitor_id, checked_at, status_code, response_time_ms, is_up, error) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (m.id, now.isoformat(), 200, 42, 1, None),
    )
    conn.commit()
    conn.close()

    out = io.StringIO()
    handle_schedule(_make_args(tmp_db_path, "json"), out=out)
    data = json.loads(out.getvalue())
    assert data[0]["seconds_until"] > 0
