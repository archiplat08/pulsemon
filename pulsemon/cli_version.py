"""CLI subcommand: version — print pulsemon version and runtime info."""
from __future__ import annotations

import argparse
import json
import platform
import sqlite3
import sys

__version__ = "0.1.0"


def add_version_parser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    """Register the `version` subcommand."""
    p = subparsers.add_parser("version", help="Show version and runtime information")
    p.add_argument(
        "--json",
        dest="json_format",
        action="store_true",
        default=False,
        help="Output as JSON",
    )


def _collect_info() -> dict:
    return {
        "pulsemon": __version__,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "sqlite": sqlite3.sqlite_version,
    }


def handle_version(args: argparse.Namespace, _out=None) -> None:
    """Print version information to *_out* (defaults to stdout)."""
    import io

    out = _out or sys.stdout
    info = _collect_info()

    if getattr(args, "json_format", False):
        out.write(json.dumps(info, indent=2))
        out.write("\n")
    else:
        out.write(f"pulsemon  {info['pulsemon']}\n")
        out.write(f"python    {info['python']}\n")
        out.write(f"platform  {info['platform']}\n")
        out.write(f"sqlite    {info['sqlite']}\n")
