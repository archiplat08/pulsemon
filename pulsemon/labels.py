"""Key-value label storage for monitors, backed by SQLite."""
from __future__ import annotations

import sqlite3
from typing import Dict


def _ensure_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS monitor_labels (
            monitor_id INTEGER NOT NULL,
            key        TEXT    NOT NULL,
            value      TEXT    NOT NULL DEFAULT '',
            PRIMARY KEY (monitor_id, key)
        )
        """
    )
    conn.commit()


def get_labels(conn: sqlite3.Connection, monitor_id: int) -> Dict[str, str]:
    """Return all labels for *monitor_id* as a plain dict."""
    _ensure_table(conn)
    rows = conn.execute(
        "SELECT key, value FROM monitor_labels WHERE monitor_id = ? ORDER BY key",
        (monitor_id,),
    ).fetchall()
    return {row[0]: row[1] for row in rows}


def set_label(
    conn: sqlite3.Connection, monitor_id: int, key: str, value: str
) -> None:
    """Insert or replace a single label."""
    _ensure_table(conn)
    conn.execute(
        """
        INSERT INTO monitor_labels (monitor_id, key, value)
        VALUES (?, ?, ?)
        ON CONFLICT(monitor_id, key) DO UPDATE SET value = excluded.value
        """,
        (monitor_id, key, value),
    )
    conn.commit()


def remove_label(conn: sqlite3.Connection, monitor_id: int, key: str) -> None:
    """Delete a label; silently does nothing if it doesn't exist."""
    _ensure_table(conn)
    conn.execute(
        "DELETE FROM monitor_labels WHERE monitor_id = ? AND key = ?",
        (monitor_id, key),
    )
    conn.commit()


def clear_labels(conn: sqlite3.Connection, monitor_id: int) -> None:
    """Remove all labels for a monitor."""
    _ensure_table(conn)
    conn.execute(
        "DELETE FROM monitor_labels WHERE monitor_id = ?",
        (monitor_id,),
    )
    conn.commit()
