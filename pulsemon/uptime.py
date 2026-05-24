"""Uptime summary helpers for multiple monitors."""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import List, Optional

from pulsemon.monitors import list_monitors
from pulsemon.history import get_uptime_percentage


@dataclass
class UptimeEntry:
    monitor_id: int
    name: str
    url: str
    uptime_pct: Optional[float]  # None if no data


def get_all_uptimes(conn: sqlite3.Connection, days: int = 30) -> List[UptimeEntry]:
    """Return uptime percentage for every monitor over the given window."""
    monitors = list_monitors(conn)
    entries: List[UptimeEntry] = []
    for m in monitors:
        pct = get_uptime_percentage(conn, m.id, days=days)
        entries.append(
            UptimeEntry(
                monitor_id=m.id,
                name=m.name,
                url=m.url,
                uptime_pct=pct,
            )
        )
    return entries


def filter_below_threshold(
    entries: List[UptimeEntry], threshold: float
) -> List[UptimeEntry]:
    """Return only entries whose uptime is below *threshold* percent.

    Entries with no data (None) are always included.
    """
    return [
        e for e in entries
        if e.uptime_pct is None or e.uptime_pct < threshold
    ]


def uptime_entry_as_dict(entry: UptimeEntry) -> dict:
    return {
        "id": entry.monitor_id,
        "name": entry.name,
        "url": entry.url,
        "uptime": entry.uptime_pct,
    }
