"""Database connection and initialisation helpers."""
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

DB_PATH: Path = Path("pulsemon.db")


def get_connection(path: Path = DB_PATH) -> sqlite3.Connection:
    """Return a new SQLite connection with row_factory set."""
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db(path: Path = DB_PATH) -> None:
    """Create all tables if they do not already exist."""
    conn = get_connection(path)
    with conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS monitors (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                url              TEXT    NOT NULL,
                name             TEXT    NOT NULL,
                interval_seconds INTEGER NOT NULL DEFAULT 60,
                timeout_seconds  INTEGER NOT NULL DEFAULT 10,
                is_active        INTEGER NOT NULL DEFAULT 1,
                created_at       TEXT    NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS check_results (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                monitor_id       INTEGER NOT NULL REFERENCES monitors(id) ON DELETE CASCADE,
                status_code      INTEGER,
                response_time_ms REAL,
                is_up            INTEGER NOT NULL,
                error_message    TEXT,
                checked_at       TEXT    NOT NULL DEFAULT (datetime('now'))
            );

            CREATE INDEX IF NOT EXISTS idx_check_results_monitor_id
                ON check_results (monitor_id);

            CREATE INDEX IF NOT EXISTS idx_check_results_checked_at
                ON check_results (checked_at);
            """
        )
    conn.close()


@contextmanager
def db_conn(path: Path = DB_PATH) -> Generator[sqlite3.Connection, None, None]:
    """Context manager that yields a connection, commits on success and rolls back on error."""
    conn = get_connection(path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
