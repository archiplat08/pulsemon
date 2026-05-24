"""CLI handler for the 'summary' subcommand — quick one-line status per monitor."""
from __future__ import annotations

import argparse
import json
import sys

from pulsemon.db import get_connection
from pulsemon.status import get_all_statuses, status_as_dict


def add_summary_parser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser("summary", help="Print a one-line status for every monitor.")
    p.add_argument("--db", default="pulsemon.db", help="Path to the SQLite database.")
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text).",
    )
    p.add_argument(
        "--only-down",
        action="store_true",
        default=False,
        help="Only show monitors that are currently DOWN.",
    )


def handle_summary(args: argparse.Namespace, out=sys.stdout) -> int:
    """Print a compact summary table of all monitors.

    Returns an exit code: 0 if all monitors are up (or none exist), 1 if any are down.
    """
    conn = get_connection(args.db)
    statuses = get_all_statuses(conn)
    conn.close()

    if args.only_down:
        statuses = [s for s in statuses if s.status == "down"]

    if args.format == "json":
        out.write(json.dumps([status_as_dict(s) for s in statuses], indent=2))
        out.write("\n")
    else:
        if not statuses:
            out.write("No monitors found.\n")
            return 0
        out.write(f"{'NAME':<30} {'STATUS':<8} {'LAST CHECKED':<22} {'LATENCY':>10}\n")
        out.write("-" * 74 + "\n")
        for s in statuses:
            latency = f"{s.latency_ms:.0f} ms" if s.latency_ms is not None else "—"
            checked = s.last_checked_at.strftime("%Y-%m-%d %H:%M:%S") if s.last_checked_at else "never"
            status_label = s.status.upper() if s.status else "UNKNOWN"
            out.write(f"{s.name:<30} {status_label:<8} {checked:<22} {latency:>10}\n")

    any_down = any(s.status == "down" for s in statuses)
    return 1 if any_down else 0
