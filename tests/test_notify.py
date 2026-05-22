"""Tests for pulsemon.notify dispatch logic."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from pulsemon.config import AlertConfig, SmtpConfig
from pulsemon.models import Monitor, CheckResult
from pulsemon.notify import notify, notify_down, notify_recovery


@pytest.fixture()
def monitor() -> Monitor:
    return Monitor(id=1, name="example", url="https://example.com", interval=60, timeout=5)


@pytest.fixture()
def result_down() -> CheckResult:
    return CheckResult(
        monitor_id=1, is_up=False, status_code=500, response_time=0.1, checked_at="2024-01-01T00:00:00"
    )


@pytest.fixture()
def result_up() -> CheckResult:
    return CheckResult(
        monitor_id=1, is_up=True, status_code=200, response_time=0.05, checked_at="2024-01-01T00:01:00"
    )


@pytest.fixture()
def alert_config_full() -> AlertConfig:
    smtp = SmtpConfig(host="smtp.example.com", port=587, username="u", password="p", from_addr="from@example.com")
    return AlertConfig(webhook_url="https://hooks.example.com/xyz", smtp=smtp, alert_email="ops@example.com")


@pytest.fixture()
def alert_config_empty() -> AlertConfig:
    return AlertConfig()


def test_notify_no_channels_configured(monitor, result_down, alert_config_empty):
    outcomes = notify(monitor, result_down, alert_config_empty)
    assert outcomes == {"webhook": False, "email": False}


def test_notify_webhook_called(monitor, result_down):
    config = AlertConfig(webhook_url="https://hooks.example.com/abc")
    with patch("pulsemon.notify.send_webhook") as mock_wh:
        outcomes = notify(monitor, result_down, config)
    mock_wh.assert_called_once()
    assert outcomes["webhook"] is True
    assert outcomes["email"] is False


def test_notify_email_called(monitor, result_down, alert_config_full):
    alert_config_full.webhook_url = None
    with patch("pulsemon.notify.send_email") as mock_mail:
        outcomes = notify(monitor, result_down, alert_config_full)
    mock_mail.assert_called_once()
    assert outcomes["email"] is True
    assert outcomes["webhook"] is False


def test_notify_both_channels(monitor, result_down, alert_config_full):
    with patch("pulsemon.notify.send_webhook"), patch("pulsemon.notify.send_email"):
        outcomes = notify(monitor, result_down, alert_config_full)
    assert outcomes["webhook"] is True
    assert outcomes["email"] is True


def test_notify_webhook_failure_does_not_raise(monitor, result_down):
    config = AlertConfig(webhook_url="https://hooks.example.com/abc")
    with patch("pulsemon.notify.send_webhook", side_effect=RuntimeError("timeout")):
        outcomes = notify(monitor, result_down, config)
    assert outcomes["webhook"] is False


def test_notify_email_failure_does_not_raise(monitor, result_down, alert_config_full):
    alert_config_full.webhook_url = None
    with patch("pulsemon.notify.send_email", side_effect=OSError("refused")):
        outcomes = notify(monitor, result_down, alert_config_full)
    assert outcomes["email"] is False


def test_notify_down_wrapper(monitor, result_down):
    config = AlertConfig(webhook_url="https://hooks.example.com/abc")
    with patch("pulsemon.notify.send_webhook") as mock_wh:
        notify_down(monitor, result_down, config)
    mock_wh.assert_called_once()


def test_notify_recovery_passes_previous(monitor, result_up, result_down, alert_config_full):
    alert_config_full.webhook_url = None
    with patch("pulsemon.notify.send_email") as mock_mail:
        notify_recovery(monitor, result_up, result_down, alert_config_full)
    mock_mail.assert_called_once()
    subject_arg = mock_mail.call_args[0][2]
    assert "UP" in subject_arg
