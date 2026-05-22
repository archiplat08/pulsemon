"""Tests for pulsemon.cli_add — unified subparser registration & dispatch."""
from __future__ import annotations

import argparse
import io

import pytest

from pulsemon.cli_add import add_all_subparsers, dispatch
from pulsemon.db import get_connection, init_db


@pytest.fixture()
def tmp_db_path(tmp_path):
    path = str(tmp_path / "test.db")
    conn = get_connection(path)
    init_db(conn)
    conn.close()
    return path


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd")
    add_all_subparsers(sub)
    return parser


def test_all_subcommands_registered():
    parser = _build_parser()
    # Each subcommand should parse without error
    parser.parse_args(["monitor", "list"])
    parser.parse_args(["status", "--format", "text"])
    parser.parse_args(["report", "--format", "text"])
    parser.parse_args(["export", "--monitor-id", "1", "--format", "json"])


def test_dispatch_monitor_list(tmp_db_path):
    parser = _build_parser()
    args = parser.parse_args(["monitor", "list"])
    rc = dispatch(args, tmp_db_path)
    assert rc == 0


def test_dispatch_status(tmp_db_path):
    parser = _build_parser()
    args = parser.parse_args(["status", "--format", "text"])
    rc = dispatch(args, tmp_db_path)
    assert rc == 0


def test_dispatch_report(tmp_db_path):
    parser = _build_parser()
    args = parser.parse_args(["report", "--format", "text"])
    rc = dispatch(args, tmp_db_path)
    assert rc == 0


def test_dispatch_unknown_cmd_returns_zero(tmp_db_path):
    args = argparse.Namespace(cmd=None)
    rc = dispatch(args, tmp_db_path)
    assert rc == 0
