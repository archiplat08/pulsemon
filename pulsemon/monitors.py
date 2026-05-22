"""CRUD operations for monitors."""
from datetime import datetime
from typing import Optional

from pulsemon.db import db_conn
from pulsemon.models import Monitor


def create_monitor(monitor: Monitor) -> Monitor:
    """Insert a new monitor and return it with its assigned id."""
    with db_conn() as conn:
        cursor = conn.execute(
            """
            INSERT INTO monitors (url, name, interval_seconds, timeout_seconds, is_active)
            VALUES (?, ?, ?, ?, ?)
            """,
            (monitor.url, monitor.name, monitor.interval_seconds,
             monitor.timeout_seconds, int(monitor.is_active)),
        )
        monitor.id = cursor.lastrowid
        row = conn.execute(
            "SELECT created_at FROM monitors WHERE id = ?", (monitor.id,)
        ).fetchone()
        monitor.created_at = datetime.fromisoformat(row["created_at"])
    return monitor


def get_monitor(monitor_id: int) -> Optional[Monitor]:
    """Fetch a single monitor by id."""
    with db_conn() as conn:
        row = conn.execute(
            "SELECT * FROM monitors WHERE id = ?", (monitor_id,)
        ).fetchone()
    if row is None:
        return None
    return _row_to_monitor(row)


def list_monitors(active_only: bool = False) -> list[Monitor]:
    """Return all monitors, optionally filtering to active ones."""
    query = "SELECT * FROM monitors"
    params: tuple = ()
    if active_only:
        query += " WHERE is_active = 1"
    with db_conn() as conn:
        rows = conn.execute(query, params).fetchall()
    return [_row_to_monitor(r) for r in rows]


def delete_monitor(monitor_id: int) -> bool:
    """Delete a monitor by id. Returns True if a row was deleted."""
    with db_conn() as conn:
        cursor = conn.execute("DELETE FROM monitors WHERE id = ?", (monitor_id,))
    return cursor.rowcount > 0


def _row_to_monitor(row) -> Monitor:
    m = Monitor(
        id=row["id"],
        url=row["url"],
        name=row["name"],
        interval_seconds=row["interval_seconds"],
        timeout_seconds=row["timeout_seconds"],
        is_active=bool(row["is_active"]),
    )
    m.created_at = datetime.fromisoformat(row["created_at"])
    return m
