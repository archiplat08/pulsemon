"""CLI subcommands for managing monitors (add, list, delete)."""
from __future__ import annotations

import argparse
import json
import sys

from pulsemon.db import get_connection
from pulsemon.models import Monitor
from pulsemon.monitors import create_monitor, delete_monitor, list_monitors


def add_monitor_parser(subparsers: argparse._SubParsersAction) -> None:
    """Register 'monitor' subcommand with its own sub-subcommands."""
    parser = subparsers.add_parser("monitor", help="Manage monitors")
    sub = parser.add_subparsers(dest="monitor_cmd", required=True)

    # add
    p_add = sub.add_parser("add", help="Add a new monitor")
    p_add.add_argument("--name", required=True, help="Human-readable name")
    p_add.add_argument("--url", required=True, help="URL to monitor")
    p_add.add_argument("--interval", type=int, default=60, help="Check interval in seconds")
    p_add.add_argument("--timeout", type=int, default=10, help="Request timeout in seconds")

    # list
    p_list = sub.add_parser("list", help="List all monitors")
    p_list.add_argument("--format", choices=["text", "json"], default="text", dest="fmt")

    # delete
    p_del = sub.add_parser("delete", help="Delete a monitor by ID")
    p_del.add_argument("id", type=int, help="Monitor ID")


def handle_monitor(args: argparse.Namespace, db_path: str, out=sys.stdout) -> int:
    """Dispatch monitor subcommand; returns exit code."""
    conn = get_connection(db_path)
    try:
        if args.monitor_cmd == "add":
            return _handle_add(args, conn, out)
        if args.monitor_cmd == "list":
            return _handle_list(args, conn, out)
        if args.monitor_cmd == "delete":
            return _handle_delete(args, conn, out)
    finally:
        conn.close()
    return 0


def _handle_add(args, conn, out) -> int:
    try:
        monitor = Monitor(
            name=args.name,
            url=args.url,
            interval=args.interval,
            timeout=args.timeout,
        )
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    created = create_monitor(conn, monitor)
    print(f"Created monitor id={created.id} name={created.name!r}", file=out)
    return 0


def _handle_list(args, conn, out) -> int:
    monitors = list_monitors(conn)
    if not monitors:
        print("No monitors configured.", file=out)
        return 0
    if args.fmt == "json":
        data = [
            {"id": m.id, "name": m.name, "url": m.url,
             "interval": m.interval, "timeout": m.timeout}
            for m in monitors
        ]
        print(json.dumps(data, indent=2), file=out)
    else:
        print(f"{'ID':<6} {'NAME':<24} {'URL':<40} {'INT':>5} {'TMO':>4}", file=out)
        print("-" * 82, file=out)
        for m in monitors:
            print(f"{m.id:<6} {m.name:<24} {m.url:<40} {m.interval:>5} {m.timeout:>4}", file=out)
    return 0


def _handle_delete(args, conn, out) -> int:
    deleted = delete_monitor(conn, args.id)
    if not deleted:
        print(f"Error: monitor id={args.id} not found.", file=sys.stderr)
        return 1
    print(f"Deleted monitor id={args.id}.", file=out)
    return 0
