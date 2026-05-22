"""CLI subcommand for viewing check history and uptime for a monitor."""

from __future__ import annotations

import argparse
import json
import sys

from pulsemon.db import get_connection
from pulsemon.history import get_check_history, get_uptime_percentage
from pulsemon.monitors import get_monitor


def add_history_parser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    """Register the 'history' subcommand."""
    parser = subparsers.add_parser(
        "history",
        help="Show check history and uptime for a monitor",
    )
    parser.add_argument("monitor_id", type=int, help="ID of the monitor")
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Maximum number of results to return (default: 20)",
    )
    parser.add_argument(
        "--format",
        dest="fmt",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    parser.set_defaults(handler=handle_history)


def handle_history(args: argparse.Namespace, out=sys.stdout) -> int:
    """Handle the 'history' subcommand."""
    with get_connection(args.db) as conn:
        monitor = get_monitor(conn, args.monitor_id)
        if monitor is None:
            print(f"Error: monitor {args.monitor_id} not found.", file=sys.stderr)
            return 1

        results = get_check_history(conn, args.monitor_id, limit=args.limit)
        uptime = get_uptime_percentage(conn, args.monitor_id)

    if args.fmt == "json":
        payload = {
            "monitor_id": monitor.id,
            "monitor_name": monitor.name,
            "uptime_percentage": uptime,
            "results": [
                {
                    "checked_at": r.checked_at,
                    "status": r.status,
                    "status_code": r.status_code,
                    "response_time_ms": r.response_time_ms,
                    "error": r.error,
                }
                for r in results
            ],
        }
        print(json.dumps(payload, indent=2), file=out)
    else:
        uptime_str = f"{uptime:.1f}%" if uptime is not None else "N/A"
        print(f"Monitor : {monitor.name} (id={monitor.id})", file=out)
        print(f"URL     : {monitor.url}", file=out)
        print(f"Uptime  : {uptime_str}", file=out)
        print("", file=out)
        if not results:
            print("No check results found.", file=out)
        else:
            print(f"{'Checked At':<25} {'Status':<6} {'Code':<6} {'RT (ms)':<10} Error", file=out)
            print("-" * 70, file=out)
            for r in results:
                code = str(r.status_code) if r.status_code is not None else "-"
                rt = f"{r.response_time_ms:.1f}" if r.response_time_ms is not None else "-"
                err = r.error or ""
                print(f"{r.checked_at:<25} {r.status:<6} {code:<6} {rt:<10} {err}", file=out)

    return 0
