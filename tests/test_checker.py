"""Tests for pulsemon.checker and pulsemon.checks."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from pulsemon.checker import check_monitor
from pulsemon.checks import get_latest_check, list_check_results, save_check_result
from pulsemon.db import init_db
from pulsemon.models import CheckResult, Monitor


@pytest.fixture()
def tmp_db():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    init_db(conn)
    yield conn
    conn.close()


def _make_monitor(**kwargs) -> Monitor:
    defaults = dict(id=1, name="Test", url="https://example.com", interval=60, timeout=10)
    defaults.update(kwargs)
    m = object.__new__(Monitor)
    m.__dict__.update(defaults)
    return m


# --- checker ---

def test_check_monitor_up():
    mock_response = MagicMock(status_code=200)
    with patch("pulsemon.checker.httpx.get", return_value=mock_response):
        result = check_monitor(_make_monitor())
    assert result.is_up is True
    assert result.status_code == 200
    assert result.error is None
    assert result.response_ms >= 0


def test_check_monitor_server_error():
    mock_response = MagicMock(status_code=500)
    with patch("pulsemon.checker.httpx.get", return_value=mock_response):
        result = check_monitor(_make_monitor())
    assert result.is_up is False
    assert result.status_code == 500


def test_check_monitor_timeout():
    import httpx
    with patch("pulsemon.checker.httpx.get", side_effect=httpx.TimeoutException("timed out")):
        result = check_monitor(_make_monitor())
    assert result.is_up is False
    assert result.status_code is None
    assert "timed out" in (result.error or "").lower()


def test_check_monitor_request_error():
    import httpx
    with patch("pulsemon.checker.httpx.get", side_effect=httpx.RequestError("connection refused")):
        result = check_monitor(_make_monitor())
    assert result.is_up is False
    assert result.error is not None


# --- checks persistence ---

def _make_result(**kwargs) -> CheckResult:
    defaults = dict(
        monitor_id=1,
        checked_at=datetime.now(timezone.utc),
        is_up=True,
        status_code=200,
        response_ms=42,
        error=None,
    )
    defaults.update(kwargs)
    return CheckResult(**defaults)


def test_save_check_result_assigns_id(tmp_db):
    result = save_check_result(_make_result(), tmp_db)
    assert result.id is not None
    assert result.id > 0


def test_get_latest_check_returns_most_recent(tmp_db):
    save_check_result(_make_result(response_ms=10), tmp_db)
    save_check_result(_make_result(response_ms=99), tmp_db)
    latest = get_latest_check(1, tmp_db)
    assert latest is not None
    assert latest.response_ms == 99


def test_get_latest_check_returns_none_when_empty(tmp_db):
    assert get_latest_check(999, tmp_db) is None


def test_list_check_results_respects_limit(tmp_db):
    for _ in range(5):
        save_check_result(_make_result(), tmp_db)
    results = list_check_results(1, tmp_db, limit=3)
    assert len(results) == 3
