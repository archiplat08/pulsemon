"""CLI subcommand: ping — run a one-off check against a monitor by name or id."""
from __future__ import annotations

import argparse
import json
import sys

from pulsemon.checker import check_monitor
from pulsemon.checks import save_check_result
from pulsemon.db import get_connection
from pulsemon.monitors import get_monitor


def add_ping_parser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser("ping", help="Run a one-off HTTP check for a monitor")
    p.add_argument("monitor_id", type=int, help="ID of the monitor to ping")
    p.add_argument(
        "--db", default="pulsemon.db", help="Path to the SQLite database file"
    )
    p.add_argument(
        "--save",
        action="store_true",
        default=False,
        help="Persist the result to the database",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )


def handle_ping(args: argparse.Namespace, out=sys.stdout) -> int:
    """Execute a single ping and optionally save the result.

    Returns an exit code: 0 if the monitor is up, 1 if down, 2 on error.
    """
    conn = get_connection(args.db)
    monitor = get_monitor(conn, args.monitor_id)
    if monitor is None:
        print(f"Error: monitor {args.monitor_id} not found.", file=sys.stderr)
        return 2

    result = check_monitor(monitor)

    if args.save:
        save_check_result(conn, result)

    if args.format == "json":
        payload = {
            "monitor_id": result.monitor_id,
            "status": result.status,
            "response_time_ms": result.response_time_ms,
            "status_code": result.status_code,
            "error": result.error,
            "checked_at": result.checked_at,
        }
        print(json.dumps(payload), file=out)
    else:
        status_label = "UP" if result.status == "up" else "DOWN"
        rt = (
            f"{result.response_time_ms:.1f} ms"
            if result.response_time_ms is not None
            else "n/a"
        )
        err = f"  error={result.error}" if result.error else ""
        print(
            f"[{status_label}] monitor={monitor.name} url={monitor.url}"
            f" response_time={rt}{err}",
            file=out,
        )

    return 0 if result.status == "up" else 1
