"""Tests for pulsemon/cli_tag.py."""
from __future__ import annotations

import argparse
import io
import json
import sqlite3
import tempfile
import os
import pytest

from pulsemon.db import init_db
from pulsemon.monitors import create_monitor
from pulsemon.models import Monitor
from pulsemon.cli_tag import add_tag_parser, handle_tag


@pytest.fixture()
def tmp_db_path(tmp_path):
    db_path = str(tmp_path / "test.db")
    conn = sqlite3.connect(db_path)
    init_db(conn)
    conn.close()
    return db_path


def _make_args(db_path, tag_action, monitor_id, tag=None, fmt="text"):
    ns = argparse.Namespace(
        db=db_path,
        tag_action=tag_action,
        monitor_id=monitor_id,
        tag=tag,
        format=fmt,
    )
    return ns


def _seed_monitor(db_path):
    conn = sqlite3.connect(db_path)
    init_db(conn)
    m = Monitor(name="example", url="https://example.com", interval=60, timeout=10)
    created = create_monitor(conn, m)
    conn.close()
    return created


def test_add_tag_parser_registers_command():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command")
    add_tag_parser(sub)
    args = parser.parse_args(["tag", "list", "1"])
    assert args.command == "tag"
    assert args.tag_action == "list"
    assert args.monitor_id == 1


def test_handle_tag_monitor_not_found(tmp_db_path):
    out = io.StringIO()
    args = _make_args(tmp_db_path, "list", monitor_id=999)
    handle_tag(args, out=out)
    assert "not found" in out.getvalue()


def test_handle_tag_add_text(tmp_db_path):
    m = _seed_monitor(tmp_db_path)
    out = io.StringIO()
    args = _make_args(tmp_db_path, "add", monitor_id=m.id, tag="production")
    handle_tag(args, out=out)
    assert "added" in out.getvalue()
    assert "production" in out.getvalue()


def test_handle_tag_add_json(tmp_db_path):
    m = _seed_monitor(tmp_db_path)
    out = io.StringIO()
    args = _make_args(tmp_db_path, "add", monitor_id=m.id, tag="critical", fmt="json")
    handle_tag(args, out=out)
    data = json.loads(out.getvalue())
    assert data["status"] == "added"
    assert data["tag"] == "critical"


def test_handle_tag_list_empty(tmp_db_path):
    m = _seed_monitor(tmp_db_path)
    out = io.StringIO()
    args = _make_args(tmp_db_path, "list", monitor_id=m.id)
    handle_tag(args, out=out)
    assert "No tags" in out.getvalue()


def test_handle_tag_list_after_add(tmp_db_path):
    m = _seed_monitor(tmp_db_path)
    add_args = _make_args(tmp_db_path, "add", monitor_id=m.id, tag="staging")
    handle_tag(add_args)
    out = io.StringIO()
    list_args = _make_args(tmp_db_path, "list", monitor_id=m.id)
    handle_tag(list_args, out=out)
    assert "staging" in out.getvalue()


def test_handle_tag_remove_existing(tmp_db_path):
    m = _seed_monitor(tmp_db_path)
    handle_tag(_make_args(tmp_db_path, "add", monitor_id=m.id, tag="beta"))
    out = io.StringIO()
    handle_tag(_make_args(tmp_db_path, "remove", monitor_id=m.id, tag="beta"), out=out)
    assert "removed" in out.getvalue()


def test_handle_tag_remove_missing(tmp_db_path):
    m = _seed_monitor(tmp_db_path)
    out = io.StringIO()
    handle_tag(_make_args(tmp_db_path, "remove", monitor_id=m.id, tag="ghost"), out=out)
    assert "not found" in out.getvalue()
