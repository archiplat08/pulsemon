"""Tests for pulsemon.cli_digest."""
from __future__ import annotations

import argparse
import io
import json
import sqlite3
from datetime import datetime, timezone

import pytest

from pulsemon.db import init_db
from pulsemon.cli_digest import add_digest_parser, handle_digest


@pytest.fixture()
def tmp_db_path(tmp_path):
    db = tmp_path / "test.db"
    conn = sqlite3.connect(str(db))
    init_db(conn)
    conn.commit()
    conn.close()
    return str(db)


def _make_args(db_path, hours=24, fmt="text"):
    ns = argparse.Namespace()
    ns.db = db_path
    ns.hours = hours
    ns.format = fmt
    return ns


def test_add_digest_parser_registers_command():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_digest_parser(sub)
    args = parser.parse_args(["digest"])
    assert args.command == "digest"


def test_add_digest_parser_defaults():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_digest_parser(sub)
    args = parser.parse_args(["digest"])
    assert args.hours == 24
    assert args.format == "text"


def test_handle_digest_text_empty_db(tmp_db_path):
    out = io.StringIO()
    rc = handle_digest(_make_args(tmp_db_path), out=out)
    assert rc == 0
    text = out.getvalue()
    assert "Digest" in text
    assert "Monitors total" in text
    assert "0" in text


def test_handle_digest_json_empty_db(tmp_db_path):
    out = io.StringIO()
    rc = handle_digest(_make_args(tmp_db_path, fmt="json"), out=out)
    assert rc == 0
    data = json.loads(out.getvalue())
    assert data["total"] == 0
    assert data["up"] == 0
    assert "avg_uptime_pct" in data


def test_handle_digest_json_with_data(tmp_db_path):
    conn = sqlite3.connect(tmp_db_path)
    now = datetime.now(timezone.utc).isoformat()
    cur = conn.execute(
        "INSERT INTO monitors (name, url, interval, timeout, created_at) VALUES (?,?,?,?,?)",
        ("m1", "http://example.com", 60, 10, now),
    )
    mid = cur.lastrowid
    conn.execute(
        "INSERT INTO check_results (monitor_id, status, response_ms, checked_at) VALUES (?,?,?,?)",
        (mid, "up", 80, now),
    )
    conn.commit()
    conn.close()

    out = io.StringIO()
    handle_digest(_make_args(tmp_db_path, fmt="json"), out=out)
    data = json.loads(out.getvalue())
    assert data["total"] == 1
    assert data["up"] == 1
    assert data["checks_in_window"] == 1
    assert data["avg_uptime_pct"] == 100.0
