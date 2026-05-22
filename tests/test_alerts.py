"""Tests for pulsemon.alerts."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from pulsemon.alerts import (
    build_alert_email_body,
    build_alert_payload,
    send_email,
    send_webhook,
)
from pulsemon.models import CheckResult, Monitor


@pytest.fixture()
def monitor() -> Monitor:
    return Monitor(id=1, name="Example", url="https://example.com", interval=60, timeout=5)


@pytest.fixture()
def result_up() -> CheckResult:
    return CheckResult(
        id=1,
        monitor_id=1,
        is_up=True,
        status_code=200,
        response_time_ms=42,
        error=None,
        checked_at="2024-01-01T00:00:00",
    )


@pytest.fixture()
def result_down() -> CheckResult:
    return CheckResult(
        id=2,
        monitor_id=1,
        is_up=False,
        status_code=None,
        response_time_ms=0,
        error="Connection refused",
        checked_at="2024-01-01T00:01:00",
    )


def test_build_alert_payload_up(monitor, result_up):
    payload = build_alert_payload(monitor, result_up)
    assert payload["status"] == "up"
    assert payload["monitor_name"] == "Example"
    assert payload["status_code"] == 200
    assert payload["error"] is None


def test_build_alert_payload_down(monitor, result_down):
    payload = build_alert_payload(monitor, result_down)
    assert payload["status"] == "down"
    assert payload["error"] == "Connection refused"
    assert payload["status_code"] is None


def test_build_alert_email_body_contains_key_fields(monitor, result_down):
    body = build_alert_email_body(monitor, result_down)
    assert "DOWN" in body
    assert monitor.url in body
    assert "Connection refused" in body


def test_send_webhook_success(monitor, result_up):
    payload = build_alert_payload(monitor, result_up)
    mock_response = MagicMock()
    mock_response.__enter__ = lambda s: s
    mock_response.__exit__ = MagicMock(return_value=False)
    with patch("urllib.request.urlopen", return_value=mock_response):
        assert send_webhook("https://hooks.example.com/notify", payload) is True


def test_send_webhook_failure(monitor, result_up):
    import urllib.error
    payload = build_alert_payload(monitor, result_up)
    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("refused")):
        assert send_webhook("https://hooks.example.com/notify", payload) is False


def test_send_email_success(monitor, result_down):
    subject = f"[pulsemon] {monitor.name} is DOWN"
    body = build_alert_email_body(monitor, result_down)
    mock_smtp = MagicMock()
    mock_smtp.__enter__ = lambda s: s
    mock_smtp.__exit__ = MagicMock(return_value=False)
    with patch("smtplib.SMTP_SSL", return_value=mock_smtp):
        result = send_email(
            smtp_host="smtp.example.com",
            smtp_port=465,
            sender="alerts@example.com",
            recipient="admin@example.com",
            subject=subject,
            body=body,
        )
    assert result is True
