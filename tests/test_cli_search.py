"""Tests for pulsemon.cli_search."""
from __future__ import annotations

import argparse
import json
import sqlite3

import pytest

from pulsemon.db import init_db
from pulsemon.monitors import create_monitor
from pulsemon.models import Monitor
from pulsemon.cli_search import add_search_parser, handle_search


@pytest.fixture()
def tmp_db_path(tmp_path):
    db = tmp_path / "test.db"
    conn = sqlite3.connect(str(db))
    conn.row_factory = sqlite3.Row
    init_db(conn)
    m = Monitor(name="WebFront", url="https://web.example.com", interval=60, timeout=10, tags="web")
    create_monitor(conn, m)
    conn.commit()
    conn.close()
    return str(db)


def _make_args(**kwargs):
    defaults = dict(query="web", field="any", fmt="text", db="pulsemon.db", handler=handle_search)
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_add_search_parser_registers_command():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_search_parser(sub)
    args = parser.parse_args(["search", "hello"])
    assert args.query == "hello"


def test_add_search_parser_field_default():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_search_parser(sub)
    args = parser.parse_args(["search", "x"])
    assert args.field == "any"


def test_handle_search_text_found(tmp_db_path, capsys):
    args = _make_args(query="WebFront", field="name", fmt="text", db=tmp_db_path)
    handle_search(args)
    out = capsys.readouterr().out
    assert "WebFront" in out
    assert "Found 1" in out


def test_handle_search_text_not_found(tmp_db_path, capsys):
    args = _make_args(query="zzznope", field="any", fmt="text", db=tmp_db_path)
    handle_search(args)
    out = capsys.readouterr().out
    assert "No monitors matched" in out


def test_handle_search_json_output(tmp_db_path, capsys):
    args = _make_args(query="web", field="any", fmt="json", db=tmp_db_path)
    handle_search(args)
    out = capsys.readouterr().out
    data = json.loads(out)
    assert isinstance(data, list)
    assert data[0]["name"] == "WebFront"


def test_handle_search_json_empty(tmp_db_path, capsys):
    args = _make_args(query="zzznope", field="any", fmt="json", db=tmp_db_path)
    handle_search(args)
    out = capsys.readouterr().out
    assert json.loads(out) == []
