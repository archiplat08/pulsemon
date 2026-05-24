"""Retry configuration storage and retrieval for monitors."""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass

_DEFAULT_MAX_RETRIES = 3
_DEFAULT_RETRY_DELAY = 5.0


@dataclass
class RetryConfig:
    monitor_id: int
    max_retries: int
    retry_delay: float


def _ensure_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS retry_configs (
            monitor_id INTEGER PRIMARY KEY,
            max_retries INTEGER NOT NULL DEFAULT 3,
            retry_delay REAL NOT NULL DEFAULT 5.0
        )
        """
    )
    conn.commit()


def get_retry_config(conn: sqlite3.Connection, monitor_id: int) -> RetryConfig:
    _ensure_table(conn)
    row = conn.execute(
        "SELECT max_retries, retry_delay FROM retry_configs WHERE monitor_id = ?",
        (monitor_id,),
    ).fetchone()
    if row is None:
        return RetryConfig(
            monitor_id=monitor_id,
            max_retries=_DEFAULT_MAX_RETRIES,
            retry_delay=_DEFAULT_RETRY_DELAY,
        )
    return RetryConfig(monitor_id=monitor_id, max_retries=row[0], retry_delay=row[1])


def set_retry_config(
    conn: sqlite3.Connection,
    monitor_id: int,
    *,
    max_retries: int = _DEFAULT_MAX_RETRIES,
    retry_delay: float = _DEFAULT_RETRY_DELAY,
) -> RetryConfig:
    if not (1 <= max_retries <= 10):
        raise ValueError(f"max_retries must be between 1 and 10, got {max_retries}")
    if retry_delay < 0:
        raise ValueError(f"retry_delay must be non-negative, got {retry_delay}")
    _ensure_table(conn)
    conn.execute(
        """
        INSERT INTO retry_configs (monitor_id, max_retries, retry_delay)
        VALUES (?, ?, ?)
        ON CONFLICT(monitor_id) DO UPDATE SET
            max_retries = excluded.max_retries,
            retry_delay = excluded.retry_delay
        """,
        (monitor_id, max_retries, retry_delay),
    )
    conn.commit()
    return RetryConfig(monitor_id=monitor_id, max_retries=max_retries, retry_delay=retry_delay)
