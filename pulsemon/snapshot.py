"""Snapshot module – build and serialise a point-in-time view of all monitors."""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional

from pulsemon.models import Monitor
from pulsemon.monitors import list_monitors
from pulsemon.status import MonitorStatus, get_monitor_status


@dataclass
class Snapshot:
    taken_at: datetime
    entries: List[MonitorStatus]


def take_snapshot(conn: sqlite3.Connection) -> Snapshot:
    """Return a Snapshot with the current status of every monitor."""
    monitors: List[Monitor] = list_monitors(conn)
    entries: List[MonitorStatus] = [
        get_monitor_status(conn, m.id) for m in monitors  # type: ignore[arg-type]
    ]
    return Snapshot(taken_at=datetime.now(timezone.utc), entries=entries)


def snapshot_as_dict(snapshot: Snapshot) -> dict:
    """Serialise a Snapshot to a plain dict suitable for JSON output."""
    from pulsemon.status import status_as_dict  # local import avoids circularity

    return {
        "taken_at": snapshot.taken_at.isoformat(),
        "total": len(snapshot.entries),
        "up": sum(1 for e in snapshot.entries if e.is_up is True),
        "down": sum(1 for e in snapshot.entries if e.is_up is False),
        "unknown": sum(1 for e in snapshot.entries if e.is_up is None),
        "monitors": [status_as_dict(e) for e in snapshot.entries],
    }


def snapshot_summary_line(snapshot: Snapshot) -> str:
    """Return a one-line human-readable summary of the snapshot."""
    total = len(snapshot.entries)
    up = sum(1 for e in snapshot.entries if e.is_up is True)
    down = sum(1 for e in snapshot.entries if e.is_up is False)
    unknown = total - up - down
    return (
        f"{snapshot.taken_at.strftime('%Y-%m-%dT%H:%M:%SZ')}  "
        f"total={total}  up={up}  down={down}  unknown={unknown}"
    )
