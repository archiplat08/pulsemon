"""Tests for pulsemon.report."""

from __future__ import annotations

import sqlite3
from datetime import datetime
from unittest.mock import patch

import pytest

from pulsemon.db import init_db
from pulsemon.report import build_monitor_summary, build_full_report, summary_as_dict, MonitorSummary
from pulsemon.models import Monitor


@pytest.fixture()
def tmp_db(tmp_path):
    db_file = tmp_path / "test.db"
    with patch("pulsemon.db.DB_PATH", str(db_file)):
        init_db()
        yield str(db_file)


def _seed(db_path: str):
    conn = sqlite3.connect(db_path)
    conn.execute(
        "INSERT INTO monitors (id, name, url, interval, timeout, created_at) "
        "VALUES ('m1', 'Alpha', 'http://alpha.test', 60, 5, '2024-01-01T00:00:00')"
    )
    conn.execute(
        "INSERT INTO check_results "
        "(monitor_id, checked_at, status_code, response_time_ms, is_up, error) "
        "VALUES ('m1', '2024-06-01T12:00:00', 200, 95, 1, NULL)"
    )
    conn.commit()
    conn.close()


def test_build_monitor_summary_shape(tmp_db):
    with patch("pulsemon.db.DB_PATH", tmp_db):
        _seed(tmp_db)
        monitor = Monitor(id="m1", name="Alpha", url="http://alpha.test", interval=60, timeout=5)
        summary = build_monitor_summary(monitor)
    assert isinstance(summary, MonitorSummary)
    assert summary.monitor_id == "m1"
    assert summary.name == "Alpha"


def test_build_monitor_summary_no_checks(tmp_db):
    with patch("pulsemon.db.DB_PATH", tmp_db):
        conn = sqlite3.connect(tmp_db)
        conn.execute(
            "INSERT INTO monitors (id, name, url, interval, timeout, created_at) "
            "VALUES ('m2', 'Beta', 'http://beta.test', 60, 5, '2024-01-01T00:00:00')"
        )
        conn.commit()
        conn.close()
        monitor = Monitor(id="m2", name="Beta", url="http://beta.test", interval=60, timeout=5)
        summary = build_monitor_summary(monitor)
    assert summary.is_up is None
    assert summary.last_checked_at is None
    assert summary.uptime_24h is None


def test_build_full_report_returns_list(tmp_db):
    with patch("pulsemon.db.DB_PATH", tmp_db):
        _seed(tmp_db)
        report = build_full_report()
    assert isinstance(report, list)
    assert len(report) == 1
    assert report[0].monitor_id == "m1"


def test_summary_as_dict_keys(tmp_db):
    with patch("pulsemon.db.DB_PATH", tmp_db):
        _seed(tmp_db)
        monitor = Monitor(id="m1", name="Alpha", url="http://alpha.test", interval=60, timeout=5)
        summary = build_monitor_summary(monitor)
        d = summary_as_dict(summary)
    expected_keys = {"monitor_id", "name", "url", "is_up", "last_checked_at",
                     "uptime_24h", "uptime_7d", "recent_results"}
    assert expected_keys == set(d.keys())


def test_summary_as_dict_recent_results_structure(tmp_db):
    with patch("pulsemon.db.DB_PATH", tmp_db):
        _seed(tmp_db)
        monitor = Monitor(id="m1", name="Alpha", url="http://alpha.test", interval=60, timeout=5)
        d = summary_as_dict(build_monitor_summary(monitor))
    assert len(d["recent_results"]) == 1
    result = d["recent_results"][0]
    assert "checked_at" in result
    assert "is_up" in result
    assert result["is_up"] is True
