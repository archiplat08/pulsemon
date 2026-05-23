"""Integration tests: purge via CLI then verify history is updated."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from pulsemon.cli_purge import handle_purge
from pulsemon.db import init_db
from pulsemon.history import get_check_history, get_uptime_percentage

import argparse


@pytest.fixture()
def tmp_db_path(tmp_path: Path) -> str:
    db_path = str(tmp_path / "integration.db")
    init_db(db_path)
    return db_path


def _insert(db_path: str, monitor_id: int, status: str, days_ago: int) -> None:
    ts = (datetime.now(tz=timezone.utc) - timedelta(days=days_ago)).isoformat()
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        INSERT INTO check_results (monitor_id, status, status_code, response_time_ms, checked_at)
        VALUES (?, ?, 200, 50, ?)
        """,
        (monitor_id, status, ts),
    )
    conn.commit()
    conn.close()


def _make_args(db_path: str, days: int = 30, dry_run: bool = False) -> argparse.Namespace:
    return argparse.Namespace(db=db_path, days=days, dry_run=dry_run)


def test_purge_clears_history(tmp_db_path: str) -> None:
    _insert(tmp_db_path, 1, "up", 60)
    _insert(tmp_db_path, 1, "up", 45)

    handle_purge(_make_args(tmp_db_path, days=30))

    results = get_check_history(tmp_db_path, monitor_id=1)
    assert results == []


def test_purge_uptime_becomes_none(tmp_db_path: str) -> None:
    _insert(tmp_db_path, 1, "up", 60)

    handle_purge(_make_args(tmp_db_path, days=30))

    pct = get_uptime_percentage(tmp_db_path, monitor_id=1)
    assert pct is None


def test_purge_leaves_recent_for_history(tmp_db_path: str) -> None:
    _insert(tmp_db_path, 1, "up", 60)   # old — should be removed
    _insert(tmp_db_path, 1, "up", 5)    # recent — should remain

    handle_purge(_make_args(tmp_db_path, days=30))

    results = get_check_history(tmp_db_path, monitor_id=1)
    assert len(results) == 1


def test_purge_uptime_reflects_remaining(tmp_db_path: str) -> None:
    _insert(tmp_db_path, 1, "up", 60)   # removed
    _insert(tmp_db_path, 1, "down", 5)  # kept
    _insert(tmp_db_path, 1, "up", 3)    # kept

    handle_purge(_make_args(tmp_db_path, days=30))

    pct = get_uptime_percentage(tmp_db_path, monitor_id=1)
    assert pct == 50.0
