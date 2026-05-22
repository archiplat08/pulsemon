"""Integration tests for report + history + checks pipeline."""
from __future__ import annotations

import sqlite3
import tempfile
import os
from datetime import datetime, timezone

import pytest

from pulsemon.db import init_db
from pulsemon.models import Monitor, CheckResult
from pulsemon.monitors import create_monitor
from pulsemon.checks import save_check_result
from pulsemon.report import build_full_report, build_monitor_summary, summary_as_dict


@pytest.fixture()
def conn():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    c = sqlite3.connect(path)
    c.row_factory = sqlite3.Row
    init_db(c)
    yield c
    c.close()
    os.unlink(path)


def _insert(conn, monitor_id: int, ok: bool, status_code: int = 200, latency: float = 0.1):
    r = CheckResult(
        monitor_id=monitor_id,
        checked_at=datetime.now(timezone.utc),
        is_up=ok,
        status_code=status_code,
        latency_ms=latency,
        error=None,
    )
    save_check_result(conn, r)


def test_full_report_aggregates_multiple_monitors(conn):
    m1 = create_monitor(conn, Monitor(name="m1", url="https://a.com", interval=60, timeout=5))
    m2 = create_monitor(conn, Monitor(name="m2", url="https://b.com", interval=60, timeout=5))

    _insert(conn, m1.id, ok=True)
    _insert(conn, m1.id, ok=True)
    _insert(conn, m2.id, ok=False, status_code=500)

    report = build_full_report(conn)
    assert len(report) == 2
    names = {s.monitor.name for s in report}
    assert names == {"m1", "m2"}


def test_summary_uptime_all_up(conn):
    m = create_monitor(conn, Monitor(name="svc", url="https://svc.io", interval=30, timeout=5))
    for _ in range(4):
        _insert(conn, m.id, ok=True)

    summary = build_monitor_summary(conn, m)
    assert summary.uptime_percentage == pytest.approx(100.0)
    assert summary.total_checks == 4
    assert summary.current_status is True


def test_summary_uptime_mixed(conn):
    m = create_monitor(conn, Monitor(name="svc", url="https://svc.io", interval=30, timeout=5))
    _insert(conn, m.id, ok=True)
    _insert(conn, m.id, ok=False)
    _insert(conn, m.id, ok=True)
    _insert(conn, m.id, ok=True)

    summary = build_monitor_summary(conn, m)
    assert summary.uptime_percentage == pytest.approx(75.0)
    assert summary.total_checks == 4


def test_summary_as_dict_structure(conn):
    m = create_monitor(conn, Monitor(name="d", url="https://d.io", interval=60, timeout=5))
    _insert(conn, m.id, ok=True)
    summary = build_monitor_summary(conn, m)
    d = summary_as_dict(summary)
    assert "monitor" in d
    assert "uptime_percentage" in d
    assert "total_checks" in d
    assert "current_status" in d
    assert "last_checked_at" in d
    assert d["monitor"]["name"] == "d"
