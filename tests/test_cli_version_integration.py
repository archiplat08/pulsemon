"""Integration tests: version subcommand wired through cli_add dispatch."""
from __future__ import annotations

import argparse
import io
import json

from pulsemon.cli_add import add_all_subparsers, dispatch
from pulsemon.cli_version import __version__


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pulsemon")
    sub = parser.add_subparsers(dest="command")
    add_all_subparsers(sub)
    return parser


def test_version_registered_in_all_subparsers():
    parser = _build_parser()
    args = parser.parse_args(["version"])
    assert args.command == "version"


def test_dispatch_version_text(tmp_path):
    parser = _build_parser()
    args = parser.parse_args(["version"])
    args.db = str(tmp_path / "pulsemon.db")
    out = io.StringIO()
    dispatch(args, _out=out)
    assert __version__ in out.getvalue()


def test_dispatch_version_json(tmp_path):
    parser = _build_parser()
    args = parser.parse_args(["version", "--json"])
    args.db = str(tmp_path / "pulsemon.db")
    out = io.StringIO()
    dispatch(args, _out=out)
    data = json.loads(out.getvalue())
    assert data["pulsemon"] == __version__
