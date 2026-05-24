"""Unit tests for pulsemon.alert_log."""
from __future__ import annotations

import sqlite3
import pytest

from pulsemon.db import init_db
from pulsemon.alert_log import (
    AlertLog,
    save_alert_log,
    list_alert_logs,
    clear_alert_logs,
    alert_log_as_dict,
)


@pytest.fixture()
def tmp_db():
    conn = sqlite3.connect(":memory:")
    init_db(conn)
    yield conn
    conn.close()


def test_save_alert_log_returns_alert_log(tmp_db):
    log = save_alert_log(tmp_db, 1, "My Monitor", "webhook", False, "timeout")
    assert isinstance(log, AlertLog)
    assert log.id is not None
    assert log.monitor_id == 1
    assert log.channel == "webhook"
    assert log.is_recovery is False
    assert log.detail == "timeout"


def test_save_alert_log_recovery_flag(tmp_db):
    log = save_alert_log(tmp_db, 2, "Other", "email", True)
    assert log.is_recovery is True
    assert log.detail is None


def test_list_alert_logs_empty(tmp_db):
    assert list_alert_logs(tmp_db) == []


def test_list_alert_logs_returns_in_desc_order(tmp_db):
    save_alert_log(tmp_db, 1, "A", "webhook", False)
    save_alert_log(tmp_db, 1, "A", "email", True)
    logs = list_alert_logs(tmp_db)
    assert len(logs) == 2
    # most recent first
    assert logs[0].sent_at >= logs[1].sent_at


def test_list_alert_logs_respects_limit(tmp_db):
    for i in range(10):
        save_alert_log(tmp_db, i, f"M{i}", "webhook", False)
    logs = list_alert_logs(tmp_db, limit=3)
    assert len(logs) == 3


def test_clear_alert_logs_returns_count(tmp_db):
    save_alert_log(tmp_db, 1, "X", "webhook", False)
    save_alert_log(tmp_db, 2, "Y", "email", True)
    deleted = clear_alert_logs(tmp_db)
    assert deleted == 2


def test_clear_alert_logs_empties_table(tmp_db):
    save_alert_log(tmp_db, 1, "X", "webhook", False)
    clear_alert_logs(tmp_db)
    assert list_alert_logs(tmp_db) == []


def test_alert_log_as_dict_keys(tmp_db):
    log = save_alert_log(tmp_db, 3, "Z", "webhook", False, "err")
    d = alert_log_as_dict(log)
    for key in ("id", "monitor_id", "monitor_name", "channel", "is_recovery", "sent_at", "detail"):
        assert key in d
    assert d["monitor_name"] == "Z"
    assert d["detail"] == "err"
