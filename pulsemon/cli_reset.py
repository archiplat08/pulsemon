"""CLI subcommand: reset — wipe all check results (optionally for a single monitor)."""

from __future__ import annotations

import argparse
import sys

from pulsemon.db import get_connection


def add_reset_parser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    """Register the `reset` subcommand."""
    parser = subparsers.add_parser(
        "reset",
        help="Delete stored check results from the database.",
    )
    parser.add_argument(
        "--db",
        default="pulsemon.db",
        help="Path to the SQLite database file (default: pulsemon.db).",
    )
    parser.add_argument(
        "--monitor-id",
        type=int,
        default=None,
        dest="monitor_id",
        help="Only delete results for this monitor ID.",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        default=False,
        help="Skip confirmation prompt.",
    )
    parser.set_defaults(func=handle_reset)


def handle_reset(args: argparse.Namespace, out=sys.stdout) -> int:
    """Execute the reset command; returns an exit code."""
    if not args.yes:
        scope = f"monitor {args.monitor_id}" if args.monitor_id else "ALL monitors"
        out.write(f"This will delete all check results for {scope}.\n")
        answer = input("Type 'yes' to confirm: ").strip().lower()
        if answer != "yes":
            out.write("Aborted.\n")
            return 1

    conn = get_connection(args.db)
    try:
        if args.monitor_id is not None:
            conn.execute(
                "DELETE FROM check_results WHERE monitor_id = ?",
                (args.monitor_id,),
            )
            conn.commit()
            deleted_scope = f"monitor {args.monitor_id}"
        else:
            conn.execute("DELETE FROM check_results")
            conn.commit()
            deleted_scope = "all monitors"
        out.write(f"Check results deleted for {deleted_scope}.\n")
    finally:
        conn.close()

    return 0
