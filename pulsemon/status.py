"""Status summary helpers for pulsemon."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from pulsemon.checks import get_latest_check
from pulsemon.monitors import list_monitors
from pulsemon.history import get_uptime_percentage
from pulsemon.db import get_connection


@dataclass
class MonitorStatus:
    monitor_id: str
    name: str
    url: str
    is_up: Optional[bool]
    last_checked_at: Optional[str]
    uptime_24h: Optional[float]
    last_status_code: Optional[int]
    last_response_ms: Optional[float]


def get_monitor_status(conn, monitor_id: str) -> Optional[MonitorStatus]:
    """Return the current status for a single monitor."""
    from pulsemon.monitors import get_monitor

    monitor = get_monitor(conn, monitor_id)
    if monitor is None:
        return None

    latest = get_latest_check(conn, monitor_id)
    uptime = get_uptime_percentage(conn, monitor_id, hours=24)

    return MonitorStatus(
        monitor_id=monitor.id,
        name=monitor.name,
        url=monitor.url,
        is_up=latest.is_up if latest else None,
        last_checked_at=latest.checked_at if latest else None,
        uptime_24h=uptime,
        last_status_code=latest.status_code if latest else None,
        last_response_ms=latest.response_ms if latest else None,
    )


def get_all_statuses(conn) -> List[MonitorStatus]:
    """Return current status for every monitor."""
    monitors = list_monitors(conn)
    return [get_monitor_status(conn, m.id) for m in monitors]


def status_as_dict(status: MonitorStatus) -> dict:
    """Serialise a MonitorStatus to a plain dict."""
    return {
        "monitor_id": status.monitor_id,
        "name": status.name,
        "url": status.url,
        "is_up": status.is_up,
        "last_checked_at": status.last_checked_at,
        "uptime_24h": status.uptime_24h,
        "last_status_code": status.last_status_code,
        "last_response_ms": status.last_response_ms,
    }
