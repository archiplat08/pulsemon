"""Incident tracking: records and queries downtime periods."""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Optional


@dataclass
class Incident:
    id: int
    monitor_id: int
    started_at: str
    resolved_at: Optional[str]


def _ensure_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS incidents (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            monitor_id  INTEGER NOT NULL,
            started_at  TEXT    NOT NULL,
            resolved_at TEXT    DEFAULT NULL
        )
        """
    )
    conn.commit()


def open_incident(conn: sqlite3.Connection, monitor_id: int, started_at: str) -> Incident:
    """Create a new unresolved incident for a monitor."""
    _ensure_table(conn)
    cur = conn.execute(
        "INSERT INTO incidents (monitor_id, started_at) VALUES (?, ?)",
        (monitor_id, started_at),
    )
    conn.commit()
    return Incident(id=cur.lastrowid, monitor_id=monitor_id, started_at=started_at, resolved_at=None)


def resolve_incident(conn: sqlite3.Connection, incident_id: int, resolved_at: str | None = None) -> None:
    """Mark an incident resolved. Uses current UTC time if resolved_at is omitted."""
    _ensure_table(conn)
    if resolved_at is None:
        from datetime import datetime, timezone
        resolved_at = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "UPDATE incidents SET resolved_at = ? WHERE id = ?",
        (resolved_at, incident_id),
    )
    conn.commit()


def list_incidents(
    conn: sqlite3.Connection,
    monitor_id: int | None = None,
    open_only: bool = False,
) -> list[Incident]:
    """Return incidents, optionally filtered by monitor or open status."""
    _ensure_table(conn)
    query = "SELECT id, monitor_id, started_at, resolved_at FROM incidents"
    params: list = []
    clauses: list[str] = []
    if monitor_id is not None:
        clauses.append("monitor_id = ?")
        params.append(monitor_id)
    if open_only:
        clauses.append("resolved_at IS NULL")
    if clauses:
        query += " WHERE " + " AND ".join(clauses)
    query += " ORDER BY started_at DESC"
    rows = conn.execute(query, params).fetchall()
    return [Incident(id=r[0], monitor_id=r[1], started_at=r[2], resolved_at=r[3]) for r in rows]


def incident_as_dict(inc: Incident) -> dict:
    return {
        "id": inc.id,
        "monitor_id": inc.monitor_id,
        "started_at": inc.started_at,
        "resolved_at": inc.resolved_at,
    }
