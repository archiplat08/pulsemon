"""Tests for pulsemon.export."""

from __future__ import annotations

import csv
import io
import json
import sqlite3
from datetime import datetime, timezone

import pytest

from pulsemon.db import init_db
from pulsemon.export import export_monitor_history, export_to_csv, export_to_json


@pytest.fixture()
def tmp_db():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    init_db(conn)
    yield conn
    conn.close()


def _insert_result(conn, monitor_id: int, status: str, response_time_ms: int = 120,
                   status_code: int = 200, error: str | None = None):
    conn.execute(
        """
        INSERT INTO check_results (monitor_id, checked_at, status, response_time_ms, status_code, error)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (monitor_id, datetime.now(timezone.utc).isoformat(), status, response_time_ms, status_code, error),
    )
    conn.commit()


def test_export_to_json_returns_list(tmp_db):
    _insert_result(tmp_db, 1, "up")
    _insert_result(tmp_db, 1, "down", status_code=500, error="server error")

    output = export_to_json(tmp_db, monitor_id=1)
    data = json.loads(output)

    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0]["status"] in ("up", "down")


def test_export_to_json_empty(tmp_db):
    output = export_to_json(tmp_db, monitor_id=99)
    assert json.loads(output) == []


def test_export_to_csv_has_header(tmp_db):
    _insert_result(tmp_db, 2, "up")

    output = export_to_csv(tmp_db, monitor_id=2)
    reader = csv.DictReader(io.StringIO(output))
    rows = list(reader)

    assert len(rows) == 1
    assert "status" in reader.fieldnames
    assert "monitor_id" in reader.fieldnames
    assert rows[0]["status"] == "up"


def test_export_to_csv_empty(tmp_db):
    output = export_to_csv(tmp_db, monitor_id=99)
    reader = csv.DictReader(io.StringIO(output))
    assert list(reader) == []


def test_export_monitor_history_json(tmp_db):
    _insert_result(tmp_db, 3, "up")
    result = export_monitor_history(tmp_db, monitor_id=3, fmt="json")
    assert json.loads(result)[0]["monitor_id"] == 3


def test_export_monitor_history_csv(tmp_db):
    _insert_result(tmp_db, 4, "down", status_code=503, error="timeout")
    result = export_monitor_history(tmp_db, monitor_id=4, fmt="csv")
    reader = csv.DictReader(io.StringIO(result))
    rows = list(reader)
    assert rows[0]["status"] == "down"
    assert rows[0]["error"] == "timeout"


def test_export_monitor_history_invalid_format(tmp_db):
    with pytest.raises(ValueError, match="Unsupported export format"):
        export_monitor_history(tmp_db, monitor_id=1, fmt="xml")  # type: ignore[arg-type]


def test_export_respects_limit(tmp_db):
    for _ in range(10):
        _insert_result(tmp_db, 5, "up")

    output = export_to_json(tmp_db, monitor_id=5, limit=3)
    assert len(json.loads(output)) == 3
