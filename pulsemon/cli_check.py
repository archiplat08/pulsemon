"""CLI subcommand: run a one-shot check against a monitor."""
from __future__ import annotations

import argparse
import json
import sys

from pulsemon.checker import check_monitor
from pulsemon.checks import save_check_result
from pulsemon.db import get_connection
from pulsemon.monitors import get_monitor


def add_check_parser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    """Register the 'check' subcommand."""
    p = subparsers.add_parser("check", help="Run an immediate check for a monitor")
    p.add_argument("monitor_id", type=int, help="ID of the monitor to check")
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        dest="fmt",
        help="Output format (default: text)",
    )
    p.add_argument(
        "--save",
        action="store_true",
        default=False,
        help="Persist the result to the database",
    )


def handle_check(args: argparse.Namespace, db_path: str) -> None:
    """Execute a check and print the result."""
    conn = get_connection(db_path)
    monitor = get_monitor(conn, args.monitor_id)
    conn.close()

    if monitor is None:
        print(f"Error: monitor {args.monitor_id} not found.", file=sys.stderr)
        sys.exit(1)

    result = check_monitor(monitor)

    if args.save:
        conn = get_connection(db_path)
        save_check_result(conn, result)
        conn.close()

    if args.fmt == "json":
        print(
            json.dumps(
                {
                    "monitor_id": result.monitor_id,
                    "status": result.status,
                    "response_time_ms": result.response_time_ms,
                    "status_code": result.status_code,
                    "error": result.error,
                    "checked_at": result.checked_at,
                },
                indent=2,
            )
        )
    else:
        icon = "✓" if result.status == "up" else "✗"
        rt = (
            f"{result.response_time_ms:.1f} ms"
            if result.response_time_ms is not None
            else "N/A"
        )
        print(
            f"{icon} Monitor #{result.monitor_id} — {result.status.upper()} "
            f"| {rt} | HTTP {result.status_code or 'N/A'}"
        )
        if result.error:
            print(f"  Error: {result.error}")
