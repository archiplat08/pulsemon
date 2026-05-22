"""Tests for pulsemon.scheduler."""

import time
import pytest
from unittest.mock import MagicMock, patch, call

from pulsemon.db import init_db, db_conn
from pulsemon.models import Monitor, CheckResult
from pulsemon.monitors import create_monitor
from pulsemon.scheduler import run_checks_once, _should_alert, Scheduler


@pytest.fixture()
def tmp_db(tmp_path):
    db_path = str(tmp_path / "test.db")
    with db_conn(db_path) as conn:
        init_db(conn)
    return db_path


def _make_monitor(**kwargs) -> Monitor:
    defaults = dict(name="example", url="https://example.com", interval=60, timeout=5)
    defaults.update(kwargs)
    return Monitor(**defaults)


def _make_result(monitor_id: int, is_up: bool, latency_ms: float = 120.0) -> CheckResult:
    return CheckResult(
        monitor_id=monitor_id,
        checked_at="2024-01-01T00:00:00+00:00",
        is_up=is_up,
        status_code=200 if is_up else 500,
        latency_ms=latency_ms,
        error=None,
    )


# ---------------------------------------------------------------------------
# _should_alert
# ---------------------------------------------------------------------------

def test_should_alert_no_previous_down():
    result = _make_result(1, is_up=False)
    assert _should_alert(None, None, result) is True


def test_should_alert_no_previous_up():
    result = _make_result(1, is_up=True)
    assert _should_alert(None, None, result) is False


def test_should_alert_status_changed():
    prev = _make_result(1, is_up=True)
    curr = _make_result(1, is_up=False)
    assert _should_alert(None, prev, curr) is True


def test_should_not_alert_same_status():
    prev = _make_result(1, is_up=True)
    curr = _make_result(1, is_up=True)
    assert _should_alert(None, prev, curr) is False


# ---------------------------------------------------------------------------
# run_checks_once
# ---------------------------------------------------------------------------

def test_run_checks_once_no_monitors(tmp_db):
    """Should complete without error when there are no monitors."""
    run_checks_once(tmp_db)


def test_run_checks_once_saves_result(tmp_db):
    with db_conn(tmp_db) as conn:
        monitor = create_monitor(conn, _make_monitor())

    fake_result = _make_result(monitor.id, is_up=True)

    with patch("pulsemon.scheduler.check_monitor", return_value=fake_result) as mock_check, \
         patch("pulsemon.scheduler.save_check_result") as mock_save:
        run_checks_once(tmp_db)

    mock_check.assert_called_once()
    mock_save.assert_called_once()


def test_run_checks_once_dispatches_alert_on_status_change(tmp_db):
    with db_conn(tmp_db) as conn:
        monitor = create_monitor(conn, _make_monitor())

    fake_result = _make_result(monitor.id, is_up=False)
    alert_cfg = {"webhook_url": "https://hooks.example.com/test"}

    with patch("pulsemon.scheduler.check_monitor", return_value=fake_result), \
         patch("pulsemon.scheduler.save_check_result"), \
         patch("pulsemon.scheduler.get_latest_check", return_value=None), \
         patch("pulsemon.scheduler.send_webhook") as mock_wh:
        run_checks_once(tmp_db, alert_config=alert_cfg)

    mock_wh.assert_called_once()


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------

def test_scheduler_runs_and_stops(tmp_db):
    call_count = []

    def fake_run(db_path, alert_config=None):
        call_count.append(1)

    with patch("pulsemon.scheduler.run_checks_once", side_effect=fake_run):
        sched = Scheduler(tmp_db, tick_seconds=1)
        sched.start()
        time.sleep(1.5)
        sched.stop(timeout=2)

    assert len(call_count) >= 1
