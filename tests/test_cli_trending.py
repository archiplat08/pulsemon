"""Tests for cli_trending.py."""
from __future__ import annotations

import argparse
import io
import json
import sqlite3
import tempfile
import os
from datetime import datetime, timezone

import pytest

from pulsemon.cli_trending import add_trending_parser, handle_trending
from pulsemon.db import init_db
from pulsemon.monitors import create_monitor
from pulsemon.models import Monitor


@pytest.fixture()
def tmp_db_path():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    conn = sqlite3.connect(path)
    init_db(conn)
    conn.close()
    yield path
    os.unlink(path)


def _make_args(db_path: str, window: int = 10, fmt: str = "text") -> argparse.Namespace:
    return argparse.Namespace(db=db_path, window=window, format=fmt, func=handle_trending)


def _seed_monitor(db_path: str) -> int:
    conn = sqlite3.connect(db_path)
    m = Monitor(name="alpha", url="http://alpha.test", interval=60, timeout=5)
    created = create_monitor(conn, m)
    mid = created.id
    now = datetime.now(timezone.utc).timestamp()
    for i in range(12):
        up = 1 if i >= 6 else 0  # older half down, recent half up
        conn.execute(
            "INSERT INTO check_results (monitor_id, checked_at, status_code, response_time_ms, is_up, error) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (mid, now - (12 - i) * 60, 200 if up else 500, 120, up, None),
        )
    conn.commit()
    conn.close()
    return mid


def test_add_trending_parser_registers_command():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_trending_parser(sub)
    args = parser.parse_args(["trending", "--db", "x.db"])
    assert args.func is handle_trending


def test_handle_trending_no_data_text(tmp_db_path):
    out = io.StringIO()
    args = _make_args(tmp_db_path)
    handle_trending(args, out=out)
    assert "No trending data" in out.getvalue()


def test_handle_trending_text_output(tmp_db_path):
    _seed_monitor(tmp_db_path)
    out = io.StringIO()
    args = _make_args(tmp_db_path, window=6)
    handle_trending(args, out=out)
    text = out.getvalue()
    assert "alpha" in text
    assert "Monitor" in text  # header row


def test_handle_trending_json_output(tmp_db_path):
    _seed_monitor(tmp_db_path)
    out = io.StringIO()
    args = _make_args(tmp_db_path, window=6, fmt="json")
    handle_trending(args, out=out)
    data = json.loads(out.getvalue())
    assert isinstance(data, list)
    assert len(data) >= 1
    assert "name" in data[0]
    assert "trend" in data[0]


def test_handle_trending_json_empty(tmp_db_path):
    out = io.StringIO()
    args = _make_args(tmp_db_path, fmt="json")
    handle_trending(args, out=out)
    data = json.loads(out.getvalue())
    assert data == []
