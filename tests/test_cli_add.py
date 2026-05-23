"""Tests for pulsemon.cli_add — subparser registration and dispatch."""
from __future__ import annotations

import argparse
from unittest.mock import patch

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


def _build_parser():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command")
    add_all_subparsers(sub)
    return parser


def test_all_subcommands_registered():
    parser = _build_parser()
    expected = {"monitor", "status", "report", "export", "history", "notify", "check"}
    # argparse stores subparser choices on the subparsers action
    subparsers_action = next(
        a for a in parser._actions if isinstance(a, argparse._SubParsersAction)
    )
    assert expected == set(subparsers_action.choices.keys())


def test_dispatch_monitor_list(tmp_db_path):
    parser = _build_parser()
    args = parser.parse_args(["monitor", "list"])
    with patch("pulsemon.cli_add.handle_monitor") as mock_h:
        dispatch(args, tmp_db_path)
        mock_h.assert_called_once_with(args, tmp_db_path)


def test_dispatch_status(tmp_db_path):
    parser = _build_parser()
    args = parser.parse_args(["status"])
    with patch("pulsemon.cli_add.handle_status") as mock_h:
        dispatch(args, tmp_db_path)
        mock_h.assert_called_once_with(args, tmp_db_path)


def test_dispatch_check(tmp_db_path):
    parser = _build_parser()
    args = parser.parse_args(["check", "1"])
    with patch("pulsemon.cli_add.handle_check") as mock_h:
        dispatch(args, tmp_db_path)
        mock_h.assert_called_once_with(args, tmp_db_path)


def test_dispatch_unknown_raises(tmp_db_path):
    args = argparse.Namespace(command="nonexistent")
    with pytest.raises(ValueError, match="Unknown command"):
        dispatch(args, tmp_db_path)
