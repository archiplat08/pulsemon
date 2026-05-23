"""History retrieval and maintenance helpers."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from typing import List, Optional

from pulsemon.checks import _row_to_check_result
from pulsemon.db import get_connection
from pulsemon.models import CheckResult


def get_check_history(
    db_path: str,
    monitor_id: int,
    limit: int = 100,
) -> List[CheckResult]:
    """Return the most recent *limit* check results for a monitor."""
    conn = get_connection(db_path)
    rows = conn.execute(
        """
        SELECT id, monitor_id, status, status_code, response_time_ms, error, checked_at
        FROM check_results
        WHERE monitor_id = ?
        ORDER BY checked_at DESC
        LIMIT ?
        """,
        (monitor_id, limit),
    ).fetchall()
    conn.close()
    return [_row_to_check_result(r) for r in rows]


def get_uptime_percentage(
    db_path: str,
    monitor_id: int,
    limit: int = 100,
) -> Optional[float]:
    """Return the uptime percentage (0-100) over the last *limit* checks."""
    conn = get_connection(db_path)
    row = conn.execute(
        """
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN status = 'up' THEN 1 ELSE 0 END) AS up_count
        FROM (
            SELECT status
            FROM check_results
            WHERE monitor_id = ?
            ORDER BY checked_at DESC
            LIMIT ?
        )
        """,
        (monitor_id, limit),
    ).fetchone()
    conn.close()
    if row is None or row[0] == 0:
        return None
    total, up_count = row
    return round((up_count / total) * 100, 2)


def purge_old_results(
    db_path: str,
    before: datetime,
) -> int:
    """Delete check results with *checked_at* older than *before*.

    Returns the number of rows deleted.
    """
    if before.tzinfo is None:
        before = before.replace(tzinfo=timezone.utc)
    conn = get_connection(db_path)
    cursor: sqlite3.Cursor = conn.execute(
        "DELETE FROM check_results WHERE checked_at < ?",
        (before.isoformat(),),
    )
    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    return deleted
