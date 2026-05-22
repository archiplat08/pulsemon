"""Notification dispatch: routes alerts to webhook and/or email based on config."""

from __future__ import annotations

import logging
from typing import Optional

from pulsemon.alerts import (
    build_alert_payload,
    build_alert_email_body,
    send_webhook,
    send_email,
)
from pulsemon.config import AlertConfig
from pulsemon.models import Monitor, CheckResult

logger = logging.getLogger(__name__)


def notify(
    monitor: Monitor,
    result: CheckResult,
    config: AlertConfig,
    previous: Optional[CheckResult] = None,
) -> dict[str, bool]:
    """Send all configured notifications for a state change.

    Returns a dict indicating which channels were attempted and succeeded.
    """
    outcomes: dict[str, bool] = {"webhook": False, "email": False}

    payload = build_alert_payload(monitor, result, previous)

    if config.webhook_url:
        try:
            send_webhook(config.webhook_url, payload)
            outcomes["webhook"] = True
            logger.info("Webhook alert sent for monitor %s", monitor.name)
        except Exception as exc:  # noqa: BLE001
            logger.error("Webhook alert failed for monitor %s: %s", monitor.name, exc)

    if config.smtp and config.alert_email:
        subject = (
            f"[pulsemon] {'DOWN' if not result.is_up else 'UP'}: {monitor.name}"
        )
        body = build_alert_email_body(monitor, result, previous)
        try:
            send_email(config.smtp, config.alert_email, subject, body)
            outcomes["email"] = True
            logger.info("Email alert sent for monitor %s", monitor.name)
        except Exception as exc:  # noqa: BLE001
            logger.error("Email alert failed for monitor %s: %s", monitor.name, exc)

    return outcomes


def notify_down(
    monitor: Monitor, result: CheckResult, config: AlertConfig
) -> dict[str, bool]:
    """Convenience wrapper: send a DOWN notification."""
    return notify(monitor, result, config)


def notify_recovery(
    monitor: Monitor,
    result: CheckResult,
    previous: CheckResult,
    config: AlertConfig,
) -> dict[str, bool]:
    """Convenience wrapper: send a recovery (UP) notification."""
    return notify(monitor, result, config, previous=previous)
