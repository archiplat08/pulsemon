"""Alert dispatching via webhook and email."""

from __future__ import annotations

import json
import logging
import smtplib
from email.message import EmailMessage
from typing import Any

import urllib.request
import urllib.error

from pulsemon.models import Monitor, CheckResult

logger = logging.getLogger(__name__)


def send_webhook(url: str, payload: dict[str, Any], timeout: int = 10) -> bool:
    """POST a JSON payload to *url*. Returns True on success."""
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout):
            return True
    except urllib.error.URLError as exc:
        logger.warning("Webhook delivery failed to %s: %s", url, exc)
        return False


def send_email(
    *,
    smtp_host: str,
    smtp_port: int,
    sender: str,
    recipient: str,
    subject: str,
    body: str,
    username: str | None = None,
    password: str | None = None,
    use_tls: bool = True,
) -> bool:
    """Send a plain-text alert email. Returns True on success."""
    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = recipient
    msg["Subject"] = subject
    msg.set_content(body)
    try:
        cls = smtplib.SMTP_SSL if use_tls else smtplib.SMTP
        with cls(smtp_host, smtp_port) as smtp:
            if username and password:
                smtp.login(username, password)
            smtp.send_message(msg)
        return True
    except smtplib.SMTPException as exc:
        logger.warning("Email delivery failed: %s", exc)
        return False


def build_alert_payload(monitor: Monitor, result: CheckResult) -> dict[str, Any]:
    """Build a structured alert payload from a monitor and its check result."""
    return {
        "monitor_id": monitor.id,
        "monitor_name": monitor.name,
        "url": monitor.url,
        "status": "up" if result.is_up else "down",
        "status_code": result.status_code,
        "response_time_ms": result.response_time_ms,
        "error": result.error,
        "checked_at": result.checked_at,
    }


def build_alert_email_body(monitor: Monitor, result: CheckResult) -> str:
    """Return a human-readable alert email body."""
    status = "UP" if result.is_up else "DOWN"
    lines = [
        f"Monitor: {monitor.name}",
        f"URL: {monitor.url}",
        f"Status: {status}",
        f"HTTP status code: {result.status_code or 'N/A'}",
        f"Response time: {result.response_time_ms} ms",
    ]
    if result.error:
        lines.append(f"Error: {result.error}")
    lines.append(f"Checked at: {result.checked_at}")
    return "\n".join(lines)
