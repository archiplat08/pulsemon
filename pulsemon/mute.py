"""Mute / unmute alert notifications for individual monitors."""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass


@dataclass
class MuteStatus:
    monitor_id: int
    muted: bool


def _ensure_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS monitor_mutes (
            monitor_id INTEGER PRIMARY KEY,
            muted       INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    conn.commit()


def get_mute_status(conn: sqlite3.Connection, monitor_id: int) -> MuteStatus:
    """Return the current mute status for *monitor_id*.

    If no row exists the monitor is considered unmuted.
    """
    _ensure_table(conn)
    row = conn.execute(
        "SELECT muted FROM monitor_mutes WHERE monitor_id = ?",
        (monitor_id,),
    ).fetchone()
    return MuteStatus(monitor_id=monitor_id, muted=bool(row[0]) if row else False)


def set_mute(conn: sqlite3.Connection, monitor_id: int, *, muted: bool) -> MuteStatus:
    """Set the mute flag for *monitor_id* and return the updated status."""
    _ensure_table(conn)
    conn.execute(
        """
        INSERT INTO monitor_mutes (monitor_id, muted)
        VALUES (?, ?)
        ON CONFLICT(monitor_id) DO UPDATE SET muted = excluded.muted
        """,
        (monitor_id, int(muted)),
    )
    conn.commit()
    return MuteStatus(monitor_id=monitor_id, muted=muted)


def is_muted(conn: sqlite3.Connection, monitor_id: int) -> bool:
    """Convenience helper — returns True when notifications are suppressed."""
    return get_mute_status(conn, monitor_id).muted
