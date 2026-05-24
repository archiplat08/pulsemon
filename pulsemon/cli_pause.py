"""CLI subcommand: pause / resume a monitor."""
from __future__ import annotations

import argparse
import sys

from pulsemon.db import get_connection
from pulsemon.monitors import get_monitor


def add_pause_parser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    """Register the *pause* subcommand."""
    p = subparsers.add_parser("pause", help="Pause or resume a monitor")
    p.add_argument("monitor_id", type=int, help="ID of the monitor")
    p.add_argument(
        "--resume",
        action="store_true",
        default=False,
        help="Resume a previously paused monitor",
    )
    p.add_argument("--db", default="pulsemon.db", help="Path to SQLite database")
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format",
    )


def handle_pause(args: argparse.Namespace, out=sys.stdout) -> int:
    """Pause or resume a monitor; returns exit code."""
    import json

    conn = get_connection(args.db)
    monitor = get_monitor(conn, args.monitor_id)
    conn.close()

    if monitor is None:
        print(f"Monitor {args.monitor_id} not found.", file=sys.stderr)
        return 1

    new_paused = not args.resume
    action = "resumed" if args.resume else "paused"

    conn = get_connection(args.db)
    try:
        conn.execute(
            "UPDATE monitors SET paused = ? WHERE id = ?",
            (1 if new_paused else 0, args.monitor_id),
        )
        conn.commit()
    finally:
        conn.close()

    if args.format == "json":
        out.write(
            json.dumps({"id": args.monitor_id, "name": monitor.name, "action": action})
            + "\n"
        )
    else:
        out.write(f"Monitor '{monitor.name}' (id={args.monitor_id}) {action}.\n")

    return 0
