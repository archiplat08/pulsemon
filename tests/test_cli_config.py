"""Tests for pulsemon.cli_config."""

from __future__ import annotations

import argparse
import io
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from pulsemon.cli_config import add_config_parser, handle_config
from pulsemon.config import AlertConfig, Config


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_args(**kwargs) -> argparse.Namespace:
    defaults = {"config": None, "format": "text", "validate": False}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _default_cfg() -> Config:
    return Config(
        db_path="pulsemon.db",
        check_interval=60,
        log_level="INFO",
        alert=AlertConfig(),
    )


# ---------------------------------------------------------------------------
# Parser registration
# ---------------------------------------------------------------------------

def test_add_config_parser_registers_command():
    root = argparse.ArgumentParser()
    sub = root.add_subparsers(dest="command")
    add_config_parser(sub)
    ns = root.parse_args(["config"])
    assert ns.command == "config"


def test_add_config_parser_validate_flag():
    root = argparse.ArgumentParser()
    sub = root.add_subparsers(dest="command")
    add_config_parser(sub)
    ns = root.parse_args(["config", "--validate"])
    assert ns.validate is True


def test_add_config_parser_json_format():
    root = argparse.ArgumentParser()
    sub = root.add_subparsers(dest="command")
    add_config_parser(sub)
    ns = root.parse_args(["config", "--format", "json"])
    assert ns.format == "json"


# ---------------------------------------------------------------------------
# handle_config — text output
# ---------------------------------------------------------------------------

def test_handle_config_text_stdout():
    out = io.StringIO()
    cfg = _default_cfg()
    with patch("pulsemon.cli_config.load_config", return_value=cfg):
        rc = handle_config(_make_args(), out=out)
    assert rc == 0
    text = out.getvalue()
    assert "db_path" in text
    assert "check_interval" in text


def test_handle_config_json_stdout():
    out = io.StringIO()
    cfg = _default_cfg()
    with patch("pulsemon.cli_config.load_config", return_value=cfg):
        rc = handle_config(_make_args(format="json"), out=out)
    assert rc == 0
    data = json.loads(out.getvalue())
    assert "db_path" in data
    assert "check_interval" in data
    assert "alert" in data


# ---------------------------------------------------------------------------
# handle_config — validate flag
# ---------------------------------------------------------------------------

def test_handle_config_validate_success():
    out = io.StringIO()
    cfg = _default_cfg()
    with patch("pulsemon.cli_config.load_config", return_value=cfg):
        rc = handle_config(_make_args(validate=True), out=out)
    assert rc == 0
    assert "valid" in out.getvalue().lower()


def test_handle_config_validate_failure_returns_1():
    with patch("pulsemon.cli_config.load_config", side_effect=ValueError("bad")):
        rc = handle_config(_make_args(validate=True))
    assert rc == 1


def test_handle_config_load_error_returns_1():
    with patch("pulsemon.cli_config.load_config", side_effect=FileNotFoundError("x")):
        rc = handle_config(_make_args())
    assert rc == 1
