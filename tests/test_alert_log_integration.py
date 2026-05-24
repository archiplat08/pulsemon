"""Integration tests: alert_log + db schema."""
from __future__ import annotations

import sqlite3
import pytest

from pulsemon.db import init_db
from pulsemon.alert_log import save_alert_log, list_alert_logs, clear_alert_logs


@pytest.fixture()
def conn():
    c = sqlite3.connect(":memory:")
    init_db(c)
    yield c
    c.close()


def _insert(conn, monitor_id: int, name: str, channel: str, recovery: bool):
    return save_alert_log(conn, monitor_id, name, channel, recovery)


def test_multiple_channels_persisted(conn):
    _insert(conn, 1, "Alpha", "webhook", False)
    _insert(conn, 1, "Alpha", "email", False)
    logs = list_alert_logs(conn)
    channels = {lg.channel for lg in logs}
    assert channels == {"webhook", "email"}


def test_recovery_and_down_mixed(conn):
    _insert(conn, 1, "Beta", "webhook", False)
    _insert(conn, 1, "Beta", "webhook", True)
    logs = list_alert_logs(conn)
    recoveries = [lg for lg in logs if lg.is_recovery]
    downs = [lg for lg in logs if not lg.is_recovery]
    assert len(recoveries) == 1
    assert len(downs) == 1


def test_clear_then_save_still_works(conn):
    _insert(conn, 2, "Gamma", "email", False)
    clear_alert_logs(conn)
    _insert(conn, 2, "Gamma", "email", True)
    logs = list_alert_logs(conn)
    assert len(logs) == 1
    assert logs[0].is_recovery is True


def test_detail_field_survives_roundtrip(conn):
    _insert(conn, 3, "Delta", "webhook", False, "Connection refused")
    logs = list_alert_logs(conn)
    assert logs[0].detail == "Connection refused"


def test_list_limit_does_not_exceed_actual_rows(conn):
    for i in range(5):
        _insert(conn, i, f"M{i}", "webhook", False)
    logs = list_alert_logs(conn, limit=100)
    assert len(logs) == 5
