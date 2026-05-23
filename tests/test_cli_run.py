"""Tests for pulsemon.cli_run."""
from __future__ import annotations

import argparse
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

from pulsemon.cli_run import add_run_parser, handle_run


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command")
    add_run_parser(sub)
    return parser


def _make_args(**kwargs) -> argparse.Namespace:
    defaults = {"config": "pulsemon.toml", "db": None, "once": False}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


# ---------------------------------------------------------------------------
# Parser registration
# ---------------------------------------------------------------------------

def test_add_run_parser_registers_command():
    parser = _build_parser()
    args = parser.parse_args(["run"])
    assert args.command == "run"


def test_add_run_parser_once_flag():
    parser = _build_parser()
    args = parser.parse_args(["run", "--once"])
    assert args.once is True


def test_add_run_parser_db_override():
    parser = _build_parser()
    args = parser.parse_args(["run", "--db", "/tmp/x.db"])
    assert args.db == "/tmp/x.db"


# ---------------------------------------------------------------------------
# handle_run — --once path
# ---------------------------------------------------------------------------

@patch("pulsemon.cli_run.Scheduler")
@patch("pulsemon.cli_run.init_db")
@patch("pulsemon.cli_run.load_config")
def test_handle_run_once_calls_run_once(mock_cfg, mock_init, MockScheduler):
    cfg = MagicMock()
    cfg.db_path = "pulsemon.db"
    mock_cfg.return_value = cfg

    sched = MagicMock()
    MockScheduler.return_value = sched

    handle_run(_make_args(once=True))

    mock_init.assert_called_once_with("pulsemon.db")
    sched.run_once.assert_called_once()
    sched.start.assert_not_called()


@patch("pulsemon.cli_run.Scheduler")
@patch("pulsemon.cli_run.init_db")
@patch("pulsemon.cli_run.load_config")
def test_handle_run_db_override_used(mock_cfg, mock_init, MockScheduler):
    cfg = MagicMock()
    cfg.db_path = "default.db"
    mock_cfg.return_value = cfg

    MockScheduler.return_value = MagicMock()

    handle_run(_make_args(db="/custom/path.db", once=True))

    mock_init.assert_called_once_with("/custom/path.db")
    MockScheduler.assert_called_once_with(db_path="/custom/path.db", config=cfg)


@patch("pulsemon.cli_run.Scheduler")
@patch("pulsemon.cli_run.init_db")
@patch("pulsemon.cli_run.load_config")
def test_handle_run_start_called_when_not_once(mock_cfg, mock_init, MockScheduler, tmp_path):
    cfg = MagicMock()
    cfg.db_path = str(tmp_path / "p.db")
    mock_cfg.return_value = cfg

    sched = MagicMock()
    # Make start() raise SystemExit so the loop terminates in the test
    sched.start.side_effect = SystemExit(0)
    MockScheduler.return_value = sched

    with pytest.raises(SystemExit):
        handle_run(_make_args(once=False))

    sched.start.assert_called_once()
    sched.run_once.assert_not_called()
