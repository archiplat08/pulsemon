"""Scheduling utilities: compute next-check times and overdue monitors."""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import List, Optional

from pulsemon.models import Monitor
from pulsemon.monitors import list_monitors
from pulsemon.checks import get_latest_check


@dataclass
class ScheduleEntry:
    monitor: Monitor
    last_checked_at: Optional[datetime]
    next_check_at: datetime
    seconds_until: int

    @property
    def is_overdue(self) -> bool:
        return self.seconds_until == 0


def get_schedule(conn: sqlite3.Connection) -> List[ScheduleEntry]:
    """Return a ScheduleEntry for every monitor in the database."""
    monitors = list_monitors(conn)
    now = datetime.now(tz=timezone.utc)
    entries: List[ScheduleEntry] = []

    for m in monitors:
        latest = get_latest_check(conn, m.id)
        if latest is None:
            next_check = now
            last_checked_at = None
        else:
            last_checked_at = latest.checked_at
            next_check = last_checked_at + timedelta(seconds=m.interval)

        delta = (next_check - now).total_seconds()
        seconds_until = max(0, int(delta))

        entries.append(
            ScheduleEntry(
                monitor=m,
                last_checked_at=last_checked_at,
                next_check_at=next_check,
                seconds_until=seconds_until,
            )
        )

    return entries


def get_overdue(conn: sqlite3.Connection) -> List[ScheduleEntry]:
    """Return only monitors whose next check time has already passed."""
    return [e for e in get_schedule(conn) if e.is_overdue]
