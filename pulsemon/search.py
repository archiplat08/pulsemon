"""Search helpers for querying monitors by name, URL, or tag."""
from __future__ import annotations

import sqlite3
from typing import List

from pulsemon.models import Monitor
from pulsemon.monitors import _row_to_monitor


def search_monitors(
    conn: sqlite3.Connection,
    query: str,
    *,
    field: str = "any",
) -> List[Monitor]:
    """Return monitors whose name, URL, or tags contain *query* (case-insensitive).

    *field* must be one of ``'name'``, ``'url'``, ``'tag'``, or ``'any'``.
    """
    term = f"%{query}%"
    if field == "name":
        sql = "SELECT * FROM monitors WHERE name LIKE ? ORDER BY name"
        params: tuple = (term,)
    elif field == "url":
        sql = "SELECT * FROM monitors WHERE url LIKE ? ORDER BY name"
        params = (term,)
    elif field == "tag":
        sql = "SELECT * FROM monitors WHERE tags LIKE ? ORDER BY name"
        params = (term,)
    else:  # any
        sql = (
            "SELECT * FROM monitors "
            "WHERE name LIKE ? OR url LIKE ? OR tags LIKE ? "
            "ORDER BY name"
        )
        params = (term, term, term)

    rows = conn.execute(sql, params).fetchall()
    return [_row_to_monitor(row) for row in rows]


def search_result_as_dict(monitor: Monitor) -> dict:
    """Serialise a Monitor to a plain dict suitable for JSON output."""
    return {
        "id": monitor.id,
        "name": monitor.name,
        "url": monitor.url,
        "interval": monitor.interval,
        "timeout": monitor.timeout,
        "tags": monitor.tags,
        "created_at": monitor.created_at,
    }
