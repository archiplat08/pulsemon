"""Aggregate summary helpers used by the CLI summary command and report module."""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import List, Optional

from pulsemon.history import get_uptime_percentage
from pulsemon.monitors import list_monitors
from pulsemon.status import get_monitor_status, MonitorStatus


@dataclass
class MonitorOverview:
    """Combines live status with uptime percentage for a single monitor."""

    monitor_id: int
    name: str
    url: str
    status: Optional[str]          # "up" | "down" | None
    latency_ms: Optional[float]
    uptime_24h: Optional[float]    # 0.0 – 100.0
    uptime_7d: Optional[float]


def build_overview(conn: sqlite3.Connection, monitor_id: int) -> MonitorOverview:
    """Return a MonitorOverview for a single monitor."""
    from pulsemon.monitors import get_monitor  # local to avoid circular

    mon = get_monitor(conn, monitor_id)
    if mon is None:
        raise ValueError(f"Monitor {monitor_id} not found")

    ms: MonitorStatus = get_monitor_status(conn, monitor_id)
    uptime_24h = get_uptime_percentage(conn, monitor_id, hours=24)
    uptime_7d = get_uptime_percentage(conn, monitor_id, hours=24 * 7)

    return MonitorOverview(
        monitor_id=monitor_id,
        name=mon.name,
        url=mon.url,
        status=ms.status,
        latency_ms=ms.latency_ms,
        uptime_24h=uptime_24h,
        uptime_7d=uptime_7d,
    )


def build_all_overviews(conn: sqlite3.Connection) -> List[MonitorOverview]:
    """Return a MonitorOverview for every monitor in the database."""
    monitors = list_monitors(conn)
    return [build_overview(conn, m.id) for m in monitors]


def overview_as_dict(o: MonitorOverview) -> dict:
    return {
        "monitor_id": o.monitor_id,
        "name": o.name,
        "url": o.url,
        "status": o.status,
        "latency_ms": o.latency_ms,
        "uptime_24h": o.uptime_24h,
        "uptime_7d": o.uptime_7d,
    }
