"""CLI sub-command: manually trigger a test notification."""

from __future__ import annotations

import argparse
import json
import sys

from pulsemon.config import load_config
from pulsemon.db import get_connection, init_db
from pulsemon.monitors import get_monitor
from pulsemon.checks import get_latest_check
from pulsemon.notify import notify


def add_notify_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("notify", help="Send a test notification for a monitor")
    p.add_argument("monitor_id", type=int, help="ID of the monitor to notify for")
    p.add_argument(
        "--config",
        default="pulsemon.toml",
        metavar="FILE",
        help="Path to config file (default: pulsemon.toml)",
    )
    p.add_argument(
        "--db",
        default="pulsemon.db",
        metavar="FILE",
        help="Path to SQLite database (default: pulsemon.db)",
    )
    p.add_argument(
        "--json",
        dest="as_json",
        action="store_true",
        help="Output result as JSON",
    )


def handle_notify(args: argparse.Namespace) -> int:
    """Execute the notify sub-command. Returns an exit code."""
    cfg = load_config(args.config)

    conn = get_connection(args.db)
    init_db(conn)

    monitor = get_monitor(conn, args.monitor_id)
    if monitor is None:
        print(f"Error: monitor {args.monitor_id} not found.", file=sys.stderr)
        conn.close()
        return 1

    result = get_latest_check(conn, args.monitor_id)
    if result is None:
        print(
            f"Error: no check results found for monitor {args.monitor_id}.",
            file=sys.stderr,
        )
        conn.close()
        return 1

    conn.close()

    outcomes = notify(monitor, result, cfg.alerts)

    if args.as_json:
        print(json.dumps({"monitor_id": monitor.id, "monitor_name": monitor.name, **outcomes}))
    else:
        lines = [f"Notification sent for monitor '{monitor.name}' (id={monitor.id}):"]
        for channel, ok in outcomes.items():
            lines.append(f"  {channel}: {'ok' if ok else 'skipped/failed'}")
        print("\n".join(lines))

    return 0
