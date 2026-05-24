"""Build a periodic digest summarising the health of all monitors."""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict


@dataclass
class Digest:
    total: int
    up: int
    down: int
    no_data: int
    checks_in_window: int
    avg_uptime_pct: float
    incidents_opened: int


def build_digest(conn: sqlite3.Connection, hours: int = 24) -> Digest:
    """Query the DB and return a Digest for the given look-back window."""
    since: datetime = datetime.now(timezone.utc) - timedelta(hours=hours)
    since_iso = since.isoformat()

    # Count monitors
    (total,) = conn.execute("SELECT COUNT(*) FROM monitors").fetchone()

    # Latest check per monitor
    rows = conn.execute(
        """
        SELECT m.id,
               (SELECT status FROM check_results
                WHERE monitor_id = m.id
                ORDER BY checked_at DESC LIMIT 1) AS last_status
        FROM monitors m
        """
    ).fetchall()

    up = sum(1 for r in rows if r[1] == "up")
    down = sum(1 for r in rows if r[1] == "down")
    no_data = sum(1 for r in rows if r[1] is None)

    # Checks within window
    (checks_in_window,) = conn.execute(
        "SELECT COUNT(*) FROM check_results WHERE checked_at >= ?",
        (since_iso,),
    ).fetchone()

    # Average uptime across all monitors in the window
    uptime_rows = conn.execute(
        """
        SELECT monitor_id,
               SUM(CASE WHEN status='up' THEN 1 ELSE 0 END) * 1.0 / COUNT(*)
        FROM check_results
        WHERE checked_at >= ?
        GROUP BY monitor_id
        """,
        (since_iso,),
    ).fetchall()
    avg_uptime_pct = (
        (sum(r[1] for r in uptime_rows) / len(uptime_rows) * 100) if uptime_rows else 0.0
    )

    # Incidents opened in window (table may not exist)
    try:
        (incidents_opened,) = conn.execute(
            "SELECT COUNT(*) FROM incidents WHERE opened_at >= ?",
            (since_iso,),
        ).fetchone()
    except sqlite3.OperationalError:
        incidents_opened = 0

    return Digest(
        total=total,
        up=up,
        down=down,
        no_data=no_data,
        checks_in_window=checks_in_window,
        avg_uptime_pct=round(avg_uptime_pct, 2),
        incidents_opened=incidents_opened,
    )


def digest_as_dict(digest: Digest) -> Dict[str, Any]:
    return {
        "total": digest.total,
        "up": digest.up,
        "down": digest.down,
        "no_data": digest.no_data,
        "checks_in_window": digest.checks_in_window,
        "avg_uptime_pct": digest.avg_uptime_pct,
        "incidents_opened": digest.incidents_opened,
    }
