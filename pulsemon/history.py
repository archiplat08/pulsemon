"""Check history queries and retention management."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import List, Optional

from pulsemon.db import db_conn
from pulsemon.checks import _row_to_check_result
from pulsemon.models import CheckResult


def get_check_history(
    monitor_id: str,
    limit: int = 100,
    since: Optional[datetime] = None,
) -> List[CheckResult]:
    """Return check results for a monitor, newest first."""
    with db_conn() as conn:
        if since is not None:
            rows = conn.execute(
                """
                SELECT id, monitor_id, checked_at, status_code, response_time_ms,
                       is_up, error
                FROM check_results
                WHERE monitor_id = ? AND checked_at >= ?
                ORDER BY checked_at DESC
                LIMIT ?
                """,
                (monitor_id, since.isoformat(), limit),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT id, monitor_id, checked_at, status_code, response_time_ms,
                       is_up, error
                FROM check_results
                WHERE monitor_id = ?
                ORDER BY checked_at DESC
                LIMIT ?
                """,
                (monitor_id, limit),
            ).fetchall()
    return [_row_to_check_result(r) for r in rows]


def get_uptime_percentage(
    monitor_id: str,
    window_hours: int = 24,
) -> Optional[float]:
    """Return uptime % over the last *window_hours* hours, or None if no data."""
    since = datetime.utcnow() - timedelta(hours=window_hours)
    with db_conn() as conn:
        row = conn.execute(
            """
            SELECT
                COUNT(*) AS total,
                SUM(CASE WHEN is_up = 1 THEN 1 ELSE 0 END) AS up_count
            FROM check_results
            WHERE monitor_id = ? AND checked_at >= ?
            """,
            (monitor_id, since.isoformat()),
        ).fetchone()
    if row is None or row["total"] == 0:
        return None
    return round(row["up_count"] / row["total"] * 100, 2)


def purge_old_results(retention_days: int = 30) -> int:
    """Delete check results older than *retention_days*. Returns deleted row count."""
    cutoff = datetime.utcnow() - timedelta(days=retention_days)
    with db_conn() as conn:
        cursor = conn.execute(
            "DELETE FROM check_results WHERE checked_at < ?",
            (cutoff.isoformat(),),
        )
    return cursor.rowcount
