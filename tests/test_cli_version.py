"""Tests for pulsemon.cli_version."""
from __future__ import annotations

import argparse
import json
import io

import pytest

from pulsemon.cli_version import (
    __version__,
    add_version_parser,
    handle_version,
    _collect_info,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command")
    add_version_parser(sub)
    return parser


def _make_args(**kwargs) -> argparse.Namespace:
    defaults = {"command": "version", "json_format": False}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


# ---------------------------------------------------------------------------
# Parser registration
# ---------------------------------------------------------------------------

def test_add_version_parser_registers_command():
    parser = _build_parser()
    args = parser.parse_args(["version"])
    assert args.command == "version"


def test_add_version_parser_json_flag():
    parser = _build_parser()
    args = parser.parse_args(["version", "--json"])
    assert args.json_format is True


# ---------------------------------------------------------------------------
# _collect_info
# ---------------------------------------------------------------------------

def test_collect_info_has_required_keys():
    info = _collect_info()
    assert "pulsemon" in info
    assert "python" in info
    assert "platform" in info
    assert "sqlite" in info


def test_collect_info_version_matches_module():
    info = _collect_info()
    assert info["pulsemon"] == __version__


# ---------------------------------------------------------------------------
# handle_version — text output
# ---------------------------------------------------------------------------

def test_handle_version_text_stdout():
    out = io.StringIO()
    handle_version(_make_args(), _out=out)
    text = out.getvalue()
    assert __version__ in text
    assert "python" in text
    assert "sqlite" in text


def test_handle_version_text_contains_platform():
    out = io.StringIO()
    handle_version(_make_args(), _out=out)
    assert "platform" in out.getvalue()


# ---------------------------------------------------------------------------
# handle_version — JSON output
# ---------------------------------------------------------------------------

def test_handle_version_json_is_valid():
    out = io.StringIO()
    handle_version(_make_args(json_format=True), _out=out)
    data = json.loads(out.getvalue())
    assert isinstance(data, dict)


def test_handle_version_json_has_all_keys():
    out = io.StringIO()
    handle_version(_make_args(json_format=True), _out=out)
    data = json.loads(out.getvalue())
    for key in ("pulsemon", "python", "platform", "sqlite"):
        assert key in data


def test_handle_version_json_version_value():
    out = io.StringIO()
    handle_version(_make_args(json_format=True), _out=out)
    data = json.loads(out.getvalue())
    assert data["pulsemon"] == __version__
