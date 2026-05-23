"""Tests for pulsemon.cli_init."""
from __future__ import annotations

import argparse
import os

import pytest

from pulsemon.cli_init import add_init_parser, handle_init


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command")
    add_init_parser(sub)
    return parser


def _make_args(tmp_path, **kwargs) -> argparse.Namespace:
    defaults = {
        "command": "init",
        "db": str(tmp_path / "pulsemon.db"),
        "force": False,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


# ---------------------------------------------------------------------------
# Parser registration
# ---------------------------------------------------------------------------

def test_add_init_parser_registers_command():
    parser = _build_parser()
    args = parser.parse_args(["init"])
    assert args.command == "init"


def test_add_init_parser_db_flag():
    parser = _build_parser()
    args = parser.parse_args(["init", "--db", "/tmp/custom.db"])
    assert args.db == "/tmp/custom.db"


def test_add_init_parser_force_flag():
    parser = _build_parser()
    args = parser.parse_args(["init", "--force"])
    assert args.force is True


# ---------------------------------------------------------------------------
# handle_init behaviour
# ---------------------------------------------------------------------------

def test_handle_init_creates_db_file(tmp_path):
    db = tmp_path / "pulsemon.db"
    args = _make_args(tmp_path, db=str(db))
    handle_init(args)
    assert db.exists()


def test_handle_init_is_idempotent(tmp_path, capsys):
    db = tmp_path / "pulsemon.db"
    args = _make_args(tmp_path, db=str(db))
    handle_init(args)
    handle_init(args)  # second call should not raise
    captured = capsys.readouterr()
    assert "already initialised" in captured.out


def test_handle_init_force_recreates_db(tmp_path):
    db = tmp_path / "pulsemon.db"
    # Create initial db
    args = _make_args(tmp_path, db=str(db), force=False)
    handle_init(args)
    mtime_first = os.path.getmtime(str(db))

    import time
    time.sleep(0.05)

    args_force = _make_args(tmp_path, db=str(db), force=True)
    handle_init(args_force)
    mtime_second = os.path.getmtime(str(db))

    assert mtime_second > mtime_first


def test_handle_init_uses_env_var(tmp_path, monkeypatch):
    db = tmp_path / "env.db"
    monkeypatch.setenv("PULSEMON_DB", str(db))
    args = argparse.Namespace(command="init", db=None, force=False)
    handle_init(args)
    assert db.exists()
