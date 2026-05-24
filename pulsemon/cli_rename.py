"""CLI handler for renaming a monitor."""
from __future__ import annotations

import argparse
import sys

from pulsemon.db import get_connection
from pulsemon.monitors import get_monitor


def add_rename_parser(subparsers: argparse._SubParsersAction) -> None:
    """Register the 'rename' subcommand."""
    p = subparsers.add_parser("rename", help="Rename an existing monitor")
    p.add_argument("monitor_id", type=int, help="ID of the monitor to rename")
    p.add_argument("new_name", help="New name for the monitor")
    p.add_argument("--db", default="pulsemon.db", help="Path to SQLite database")
    p.add_argument(
        "--json", dest="json_output", action="store_true", help="Output result as JSON"
    )


def handle_rename(args: argparse.Namespace, out=sys.stdout, err=sys.stderr) -> int:
    """Rename a monitor by ID.

    Returns 0 on success, 1 on failure.
    """
    new_name = args.new_name.strip()
    if not new_name:
        err.write("Error: new_name must not be empty.\n")
        return 1

    conn = get_connection(args.db)
    try:
        monitor = get_monitor(conn, args.monitor_id)
        if monitor is None:
            err.write(f"Error: monitor {args.monitor_id} not found.\n")
            return 1

        old_name = monitor.name
        conn.execute(
            "UPDATE monitors SET name = ? WHERE id = ?",
            (new_name, args.monitor_id),
        )
        conn.commit()
    finally:
        conn.close()

    if getattr(args, "json_output", False):
        import json

        out.write(
            json.dumps(
                {"id": args.monitor_id, "old_name": old_name, "new_name": new_name}
            )
            + "\n"
        )
    else:
        out.write(
            f"Monitor {args.monitor_id} renamed: '{old_name}' → '{new_name}'\n"
        )

    return 0
