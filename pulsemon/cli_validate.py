"""CLI subcommand: validate — check a monitor's URL is reachable without persisting."""
from __future__ import annotations

import argparse
import json
import sys

from pulsemon.checker import check_monitor
from pulsemon.db import get_connection
from pulsemon.monitors import get_monitor


def add_validate_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser(
        "validate",
        help="Probe a monitor's URL once and report the result (nothing is saved).",
    )
    p.add_argument("monitor_id", type=int, help="ID of the monitor to validate.")
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        dest="fmt",
        help="Output format (default: text).",
    )
    p.add_argument("--db", default="pulsemon.db", help="Path to the SQLite database.")


def handle_validate(args: argparse.Namespace, out=sys.stdout) -> int:
    """Run a one-shot probe and print the result.  Returns exit code."""
    conn = get_connection(args.db)
    monitor = get_monitor(conn, args.monitor_id)
    conn.close()

    if monitor is None:
        print(f"Error: monitor {args.monitor_id} not found.", file=sys.stderr)
        return 1

    result = check_monitor(monitor)

    if args.fmt == "json":
        payload = {
            "monitor_id": monitor.id,
            "name": monitor.name,
            "url": monitor.url,
            "is_up": result.is_up,
            "status_code": result.status_code,
            "response_time_ms": result.response_time_ms,
            "error": result.error,
        }
        print(json.dumps(payload), file=out)
    else:
        status = "UP" if result.is_up else "DOWN"
        code_str = str(result.status_code) if result.status_code else "n/a"
        rt_str = (
            f"{result.response_time_ms:.1f} ms"
            if result.response_time_ms is not None
            else "n/a"
        )
        print(
            f"[{status}] {monitor.name} ({monitor.url})"
            f"  status={code_str}  response_time={rt_str}",
            file=out,
        )
        if result.error:
            print(f"  error: {result.error}", file=out)

    return 0 if result.is_up else 2
