"""CLI subcommand: trending — show monitors with improving or degrading uptime."""
from __future__ import annotations

import argparse
import json
from typing import Any

from pulsemon.db import get_connection
from pulsemon.trending import get_trending


def add_trending_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("trending", help="Show monitors with uptime trend changes")
    p.add_argument("--db", default="pulsemon.db", help="Path to SQLite database")
    p.add_argument(
        "--window",
        type=int,
        default=10,
        help="Number of recent checks to compare (default: 10)",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    p.set_defaults(func=handle_trending)


def handle_trending(args: argparse.Namespace, out: Any = None) -> None:
    import sys

    out = out or sys.stdout

    with get_connection(args.db) as conn:
        entries = get_trending(conn, window=args.window)

    if args.format == "json":
        out.write(json.dumps([e.__dict__ for e in entries], indent=2))
        out.write("\n")
        return

    if not entries:
        out.write("No trending data available.\n")
        return

    out.write(f"{'Monitor':<30} {'Trend':<12} {'Recent Uptime':>14} {'Older Uptime':>13}\n")
    out.write("-" * 72 + "\n")
    for e in entries:
        recent = f"{e.recent_uptime:.1f}%" if e.recent_uptime is not None else "N/A"
        older = f"{e.older_uptime:.1f}%" if e.older_uptime is not None else "N/A"
        out.write(f"{e.name:<30} {e.trend:<12} {recent:>14} {older:>13}\n")
