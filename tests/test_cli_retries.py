"""Tests for pulsemon.cli_retries module."""
from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path

import pytest

from pulsemon.cli_retries import add_retries_parser, handle_retries
from pulsemon.retries import set_retry_config


@pytest.fixture
def tmp_db_path(tmp_path):
    db = tmp_path / "test.db"
    return str(db)


def _make_args(**kwargs) -> argparse.Namespace:
    defaults = {"monitor_id": 1, "max_retries": None, "retry_delay": None, "format": "text", "db": ":memory:"}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_add_retries_parser_registers_command():
    root = argparse.ArgumentParser()
    sub = root.add_subparsers(dest="command")
    add_retries_parser(sub)
    parsed = root.parse_args(["retries", "5"])
    assert parsed.monitor_id == 5


def test_handle_retries_shows_defaults(tmp_db_path, capsys):
    args = _make_args(db=tmp_db_path, monitor_id=1)
    handle_retries(args)
    out = capsys.readouterr().out
    assert "max_retries=3" in out
    assert "retry_delay=5.0" in out


def test_handle_retries_json_format(tmp_db_path, capsys):
    args = _make_args(db=tmp_db_path, monitor_id=7, format="json")
    handle_retries(args)
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["monitor_id"] == 7
    assert "max_retries" in data
    assert "retry_delay" in data


def test_handle_retries_set_max(tmp_db_path, capsys):
    args = _make_args(db=tmp_db_path, monitor_id=1, max_retries=6)
    handle_retries(args)
    out = capsys.readouterr().out
    assert "max_retries=6" in out


def test_handle_retries_set_delay(tmp_db_path, capsys):
    args = _make_args(db=tmp_db_path, monitor_id=1, retry_delay=15.0)
    handle_retries(args)
    out = capsys.readouterr().out
    assert "retry_delay=15.0" in out


def test_handle_retries_set_both_json(tmp_db_path, capsys):
    args = _make_args(db=tmp_db_path, monitor_id=3, max_retries=4, retry_delay=2.5, format="json")
    handle_retries(args)
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["max_retries"] == 4
    assert data["retry_delay"] == 2.5
