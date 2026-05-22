"""HTTP check execution for monitors."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

import httpx

from pulsemon.models import CheckResult, Monitor


def check_monitor(monitor: Monitor) -> CheckResult:
    """Perform an HTTP GET request for *monitor* and return a CheckResult."""
    started_at = datetime.now(timezone.utc)
    t0 = time.monotonic()

    try:
        response = httpx.get(
            monitor.url,
            timeout=monitor.timeout,
            follow_redirects=True,
        )
        elapsed_ms = int((time.monotonic() - t0) * 1000)
        status_code: Optional[int] = response.status_code
        is_up = response.status_code < 400
        error: Optional[str] = None
    except httpx.TimeoutException:
        elapsed_ms = int((time.monotonic() - t0) * 1000)
        status_code = None
        is_up = False
        error = "Request timed out"
    except httpx.RequestError as exc:
        elapsed_ms = int((time.monotonic() - t0) * 1000)
        status_code = None
        is_up = False
        error = str(exc)

    return CheckResult(
        monitor_id=monitor.id,  # type: ignore[arg-type]
        checked_at=started_at,
        is_up=is_up,
        status_code=status_code,
        response_ms=elapsed_ms,
        error=error,
    )
