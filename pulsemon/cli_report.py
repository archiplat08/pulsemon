"""CLI subcommand: report — print a full uptime report."""
from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from pulsemon.db import get_connection
from pulsemon.report import build_full_report, summary_as_dict


def add_report_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register the 'report' subcommand."""
    parser = subparsers.add_parser(
        "report",
        help="Print a full uptime report for all monitors.",
    )
    parser.add_argument(
        "--db",
        default="pulsemon.db",
        help="Path to the SQLite database file (default: pulsemon.db).",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Number of recent checks to include per monitor (default: 50).",
    )


def handle_report(args: argparse.Namespace, out=sys.stdout) -> None:  # type: ignore[assignment]
    """Execute the 'report' subcommand."""
    conn = get_connection(args.db)
    summaries = build_full_report(conn, limit=args.limit)

    if args.format == "json":
        data: list[dict[str, Any]] = [summary_as_dict(s) for s in summaries]
        json.dump(data, out, indent=2, default=str)
        out.write("\n")
        return

    # text format
    if not summaries:
        out.write("No monitors found.\n")
        return

    for s in summaries:
        status_label = "UP" if s.current_status else "DOWN" if s.current_status is False else "UNKNOWN"
        out.write(f"Monitor : {s.monitor.name}\n")
        out.write(f"  URL   : {s.monitor.url}\n")
        out.write(f"  Status: {status_label}\n")
        uptime = f"{s.uptime_percentage:.1f}%" if s.uptime_percentage is not None else "N/A"
        out.write(f"  Uptime: {uptime}\n")
        out.write(f"  Checks: {s.total_checks}\n")
        if s.last_checked_at:
            out.write(f"  Last checked: {s.last_checked_at}\n")
        out.write("\n")
