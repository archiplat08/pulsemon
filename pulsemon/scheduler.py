"""Scheduler: periodically runs checks for all monitors and triggers alerts."""

import logging
import threading
import time
from datetime import datetime, timezone

from pulsemon.alerts import build_alert_payload, build_alert_email_body, send_webhook, send_email
from pulsemon.checker import check_monitor
from pulsemon.checks import save_check_result, get_latest_check
from pulsemon.db import db_conn
from pulsemon.monitors import list_monitors

logger = logging.getLogger(__name__)


def _should_alert(monitor, previous, current) -> bool:
    """Return True when status has changed (up->down or down->up)."""
    if previous is None:
        return not current.is_up
    return previous.is_up != current.is_up


def run_checks_once(db_path: str, alert_config: dict | None = None) -> None:
    """Run a single check cycle for every monitor in the database."""
    with db_conn(db_path) as conn:
        monitors = list_monitors(conn)

    for monitor in monitors:
        try:
            with db_conn(db_path) as conn:
                previous = get_latest_check(conn, monitor.id)

            result = check_monitor(monitor)

            with db_conn(db_path) as conn:
                save_check_result(conn, result)

            logger.info(
                "checked monitor=%s status=%s latency=%.3fs",
                monitor.name,
                "up" if result.is_up else "down",
                result.latency_ms / 1000,
            )

            if alert_config and _should_alert(monitor, previous, result):
                _dispatch_alerts(monitor, result, alert_config)

        except Exception as exc:  # pragma: no cover
            logger.exception("error checking monitor %s: %s", monitor.name, exc)


def _dispatch_alerts(monitor, result, alert_config: dict) -> None:
    payload = build_alert_payload(monitor, result)

    if webhook_url := alert_config.get("webhook_url"):
        try:
            send_webhook(webhook_url, payload)
        except Exception as exc:
            logger.warning("webhook alert failed for %s: %s", monitor.name, exc)

    if smtp_cfg := alert_config.get("smtp"):
        subject = f"[pulsemon] {monitor.name} is {'UP' if result.is_up else 'DOWN'}"
        body = build_alert_email_body(monitor, result)
        try:
            send_email(smtp_cfg, subject, body)
        except Exception as exc:
            logger.warning("email alert failed for %s: %s", monitor.name, exc)


class Scheduler:
    """Background thread that runs check cycles at a fixed tick interval."""

    def __init__(self, db_path: str, tick_seconds: int = 30, alert_config: dict | None = None):
        self.db_path = db_path
        self.tick_seconds = tick_seconds
        self.alert_config = alert_config
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True, name="pulsemon-scheduler")
        self._thread.start()
        logger.info("scheduler started (tick=%ds)", self.tick_seconds)

    def stop(self, timeout: float = 5.0) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=timeout)
        logger.info("scheduler stopped")

    def _loop(self) -> None:
        while not self._stop_event.is_set():
            run_checks_once(self.db_path, self.alert_config)
            self._stop_event.wait(timeout=self.tick_seconds)
