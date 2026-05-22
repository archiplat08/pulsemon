"""Database initialization and connection management for pulsemon."""

import sqlite3
import os
from contextlib import contextmanager

DEFAULT_DB_PATH = os.environ.get("PULSEMON_DB_PATH", "pulsemon.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS monitors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    url TEXT NOT NULL,
    interval_seconds INTEGER NOT NULL DEFAULT 60,
    timeout_seconds INTEGER NOT NULL DEFAULT 10,
    enabled INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS checks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    monitor_id INTEGER NOT NULL,
    checked_at TEXT NOT NULL DEFAULT (datetime('now')),
    status_code INTEGER,
    response_time_ms REAL,
    is_up INTEGER NOT NULL,
    error TEXT,
    FOREIGN KEY (monitor_id) REFERENCES monitors(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    monitor_id INTEGER NOT NULL,
    triggered_at TEXT NOT NULL DEFAULT (datetime('now')),
    resolved_at TEXT,
    kind TEXT NOT NULL,
    FOREIGN KEY (monitor_id) REFERENCES monitors(id) ON DELETE CASCADE
);
"""


def get_connection(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Return a new SQLite connection with WAL mode and foreign keys enabled."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db(db_path: str = DEFAULT_DB_PATH) -> None:
    """Create all tables if they do not already exist."""
    with get_connection(db_path) as conn:
        conn.executescript(SCHEMA)


@contextmanager
def db_conn(db_path: str = DEFAULT_DB_PATH):
    """Context manager that yields a connection and commits/rolls back automatically."""
    conn = get_connection(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
