"""Persistence layer for alert delivery history."""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class AlertLog:
    id: int
    monitor_id: int
    monitor_name: str
    channel: str          # "webhook" | "email"
    is_recovery: bool
    sent_at: datetime
    detail: Optional[str] = None


def save_alert_log(
    conn: sqlite3.Connection,
    monitor_id: int,
    monitor_name: str,
    channel: str,
    is_recovery: bool,
    detail: Optional[str] = None,
) -> AlertLog:
    now = datetime.utcnow().isoformat()
    cur = conn.execute(
        """
        INSERT INTO alert_logs (monitor_id, monitor_name, channel, is_recovery, sent_at, detail)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (monitor_id, monitor_name, channel, int(is_recovery), now, detail),
    )
    conn.commit()
    return AlertLog(
        id=cur.lastrowid,
        monitor_id=monitor_id,
        monitor_name=monitor_name,
        channel=channel,
        is_recovery=is_recovery,
        sent_at=now,
        detail=detail,
    )


def list_alert_logs(conn: sqlite3.Connection, limit: int = 50) -> List[AlertLog]:
    rows = conn.execute(
        "SELECT id, monitor_id, monitor_name, channel, is_recovery, sent_at, detail "
        "FROM alert_logs ORDER BY sent_at DESC LIMIT ?",
        (limit,),
    ).fetchall()
    return [_row_to_log(r) for r in rows]


def clear_alert_logs(conn: sqlite3.Connection) -> int:
    cur = conn.execute("DELETE FROM alert_logs")
    conn.commit()
    return cur.rowcount


def _row_to_log(row: sqlite3.Row) -> AlertLog:
    return AlertLog(
        id=row[0],
        monitor_id=row[1],
        monitor_name=row[2],
        channel=row[3],
        is_recovery=bool(row[4]),
        sent_at=row[5],
        detail=row[6],
    )


def alert_log_as_dict(log: AlertLog) -> dict:
    return {
        "id": log.id,
        "monitor_id": log.monitor_id,
        "monitor_name": log.monitor_name,
        "channel": log.channel,
        "is_recovery": log.is_recovery,
        "sent_at": str(log.sent_at),
        "detail": log.detail,
    }
