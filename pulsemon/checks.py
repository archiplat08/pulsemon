"""Persistence helpers for CheckResult records."""

from __future__ import annotations

from typing import List, Optional

from pulsemon.db import db_conn
from pulsemon.models import CheckResult


def save_check_result(result: CheckResult, conn) -> CheckResult:
    """Insert a CheckResult row and return it with the generated id."""
    with db_conn(conn) as c:
        cur = c.execute(
            """
            INSERT INTO check_results
                (monitor_id, checked_at, is_up, status_code, response_ms, error)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                result.monitor_id,
                result.checked_at.isoformat(),
                int(result.is_up),
                result.status_code,
                result.response_ms,
                result.error,
            ),
        )
    return CheckResult(
        id=cur.lastrowid,
        monitor_id=result.monitor_id,
        checked_at=result.checked_at,
        is_up=result.is_up,
        status_code=result.status_code,
        response_ms=result.response_ms,
        error=result.error,
    )


def get_latest_check(monitor_id: int, conn) -> Optional[CheckResult]:
    """Return the most recent CheckResult for *monitor_id*, or None."""
    row = conn.execute(
        """
        SELECT id, monitor_id, checked_at, is_up, status_code, response_ms, error
        FROM check_results
        WHERE monitor_id = ?
        ORDER BY checked_at DESC
        LIMIT 1
        """,
        (monitor_id,),
    ).fetchone()
    return _row_to_check_result(row) if row else None


def list_check_results(monitor_id: int, conn, limit: int = 50) -> List[CheckResult]:
    """Return up to *limit* most recent CheckResults for *monitor_id*."""
    rows = conn.execute(
        """
        SELECT id, monitor_id, checked_at, is_up, status_code, response_ms, error
        FROM check_results
        WHERE monitor_id = ?
        ORDER BY checked_at DESC
        LIMIT ?
        """,
        (monitor_id, limit),
    ).fetchall()
    return [_row_to_check_result(r) for r in rows]


def _row_to_check_result(row) -> CheckResult:
    from datetime import datetime, timezone

    return CheckResult(
        id=row["id"],
        monitor_id=row["monitor_id"],
        checked_at=datetime.fromisoformat(row["checked_at"]).replace(tzinfo=timezone.utc),
        is_up=bool(row["is_up"]),
        status_code=row["status_code"],
        response_ms=row["response_ms"],
        error=row["error"],
    )
