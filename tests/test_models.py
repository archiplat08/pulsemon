"""Tests for pulsemon.models."""
import pytest
from datetime import datetime
from pulsemon.models import Monitor, CheckResult


def test_monitor_valid():
    m = Monitor(url="https://example.com", name="Example", interval_seconds=30)
    assert m.url == "https://example.com"
    assert m.is_active is True


def test_monitor_rejects_short_interval():
    with pytest.raises(ValueError, match="interval_seconds"):
        Monitor(url="https://example.com", name="X", interval_seconds=5)


def test_monitor_rejects_bad_timeout():
    with pytest.raises(ValueError, match="timeout_seconds"):
        Monitor(url="https://example.com", name="X", timeout_seconds=0)


def test_monitor_rejects_non_http_url():
    with pytest.raises(ValueError, match="url"):
        Monitor(url="ftp://example.com", name="FTP")


def test_monitor_rejects_empty_name():
    with pytest.raises(ValueError, match="name"):
        Monitor(url="https://example.com", name="   ")


def test_check_result_defaults():
    now_before = datetime.utcnow()
    result = CheckResult(
        monitor_id=1,
        status_code=200,
        response_time_ms=42.5,
        is_up=True,
    )
    assert result.is_up is True
    assert result.error_message is None
    assert result.checked_at >= now_before


def test_check_result_down_with_error():
    result = CheckResult(
        monitor_id=2,
        status_code=None,
        response_time_ms=None,
        is_up=False,
        error_message="Connection refused",
    )
    assert result.is_up is False
    assert result.error_message == "Connection refused"
