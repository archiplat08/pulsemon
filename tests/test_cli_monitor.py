"""Tests for pulsemon.cli_monitor."""
from __future__ import annotations

import argparse
import io
import json
import os
import tempfile

import pytest

from pulsemon.cli_monitor import add_monitor_parser, handle_monitor
from pulsemon.db import get_connection, init_db


@pytest.fixture()
def tmp_db_path(tmp_path):
    path = str(tmp_path / "test.db")
    conn = get_connection(path)
    init_db(conn)
    conn.close()
    return path


def _make_args(**kwargs) -> argparse.Namespace:
    defaults = dict(monitor_cmd="list", fmt="text")
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_add_monitor_parser_registers_command():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd")
    add_monitor_parser(sub)
    args = parser.parse_args(["monitor", "list"])
    assert args.cmd == "monitor"
    assert args.monitor_cmd == "list"


def test_handle_monitor_add_creates_monitor(tmp_db_path):
    args = _make_args(
        monitor_cmd="add",
        name="Google",
        url="https://google.com",
        interval=60,
        timeout=10,
    )
    out = io.StringIO()
    rc = handle_monitor(args, tmp_db_path, out=out)
    assert rc == 0
    assert "Created monitor" in out.getvalue()
    assert "id=1" in out.getvalue()


def test_handle_monitor_add_invalid_url(tmp_db_path):
    args = _make_args(
        monitor_cmd="add",
        name="Bad",
        url="ftp://not-http.com",
        interval=60,
        timeout=10,
    )
    out = io.StringIO()
    rc = handle_monitor(args, tmp_db_path, out=out)
    assert rc == 1


def test_handle_monitor_list_empty(tmp_db_path):
    args = _make_args(monitor_cmd="list", fmt="text")
    out = io.StringIO()
    rc = handle_monitor(args, tmp_db_path, out=out)
    assert rc == 0
    assert "No monitors" in out.getvalue()


def test_handle_monitor_list_json(tmp_db_path):
    # add one first
    add_args = _make_args(
        monitor_cmd="add", name="Test", url="https://example.com",
        interval=30, timeout=5,
    )
    handle_monitor(add_args, tmp_db_path)

    args = _make_args(monitor_cmd="list", fmt="json")
    out = io.StringIO()
    rc = handle_monitor(args, tmp_db_path, out=out)
    assert rc == 0
    data = json.loads(out.getvalue())
    assert isinstance(data, list)
    assert data[0]["name"] == "Test"


def test_handle_monitor_delete_existing(tmp_db_path):
    add_args = _make_args(
        monitor_cmd="add", name="ToDelete", url="https://example.com",
        interval=60, timeout=10,
    )
    handle_monitor(add_args, tmp_db_path)

    args = _make_args(monitor_cmd="delete", id=1)
    out = io.StringIO()
    rc = handle_monitor(args, tmp_db_path, out=out)
    assert rc == 0
    assert "Deleted" in out.getvalue()


def test_handle_monitor_delete_missing(tmp_db_path):
    args = _make_args(monitor_cmd="delete", id=999)
    out = io.StringIO()
    rc = handle_monitor(args, tmp_db_path, out=out)
    assert rc == 1
