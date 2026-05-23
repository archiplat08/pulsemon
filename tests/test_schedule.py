"""Tests for pulsemon/schedule.py."""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone, timedelta

import pytest

from pulsemon.db import init_db
from pulsemon.monitors import create_monitor
from pulsemon.schedule import get_schedule, get_overdue, ScheduleEntry


@pytest.fixture()
def tmp_db():
    conn = sqlite3.connect(":memory:")
    init_db(conn)
    yield conn
    conn.close()


def _make_monitor(conn, name="test", url="http://example.com", interval=60):
    return create_monitor(conn, name=name, url=url, interval=interval)


def _insert_result(conn, monitor_id: int, checked_at: datetime, is_up: bool = True):
    conn.execute(
        "INSERT INTO check_results (monitor_id, checked_at, status_code, response_time_ms, is_up, error) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (monitor_id, checked_at.isoformat(), 200 if is_up else 500, 10, int(is_up), None),
    )
    conn.commit()


def test_get_schedule_empty(tmp_db):
    assert get_schedule(tmp_db) == []


def test_get_schedule_no_checks_is_overdue(tmp_db):
    m = _make_monitor(tmp_db)
    entries = get_schedule(tmp_db)
    assert len(entries) == 1
    e = entries[0]
    assert e.monitor.id == m.id
    assert e.last_checked_at is None
    assert e.is_overdue is True
    assert e.seconds_until == 0


def test_get_schedule_recent_check_not_overdue(tmp_db):
    m = _make_monitor(tmp_db, interval=300)
    now = datetime.now(tz=timezone.utc)
    _insert_result(tmp_db, m.id, now)
    entries = get_schedule(tmp_db)
    assert len(entries) == 1
    e = entries[0]
    assert e.is_overdue is False
    assert e.seconds_until > 0


def test_get_schedule_old_check_is_overdue(tmp_db):
    m = _make_monitor(tmp_db, interval=60)
    old_time = datetime.now(tz=timezone.utc) - timedelta(seconds=120)
    _insert_result(tmp_db, m.id, old_time)
    entries = get_schedule(tmp_db)
    assert entries[0].is_overdue is True


def test_get_overdue_filters_correctly(tmp_db):
    m1 = _make_monitor(tmp_db, name="overdue", interval=60)
    m2 = _make_monitor(tmp_db, name="fresh", interval=300)

    old = datetime.now(tz=timezone.utc) - timedelta(seconds=200)
    recent = datetime.now(tz=timezone.utc)

    _insert_result(tmp_db, m1.id, old)
    _insert_result(tmp_db, m2.id, recent)

    overdue = get_overdue(tmp_db)
    assert len(overdue) == 1
    assert overdue[0].monitor.name == "overdue"


def test_schedule_entry_next_check_at(tmp_db):
    m = _make_monitor(tmp_db, interval=120)
    checked_at = datetime.now(tz=timezone.utc) - timedelta(seconds=30)
    _insert_result(tmp_db, m.id, checked_at)
    entries = get_schedule(tmp_db)
    e = entries[0]
    expected_next = checked_at + timedelta(seconds=120)
    diff = abs((e.next_check_at - expected_next).total_seconds())
    assert diff < 1
