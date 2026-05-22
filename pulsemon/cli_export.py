"""CLI helpers for the export sub-command."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pulsemon.db import get_connection, init_db
from pulsemon.export import export_monitor_history


def add_export_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register the ``export`` sub-command on *subparsers*."""
    p = subparsers.add_parser(
        "export",
        help="Export check history for a monitor to JSON or CSV.",
    )
    p.add_argument("monitor_id", type=int, help="ID of the monitor to export.")
    p.add_argument(
        "--format",
        dest="fmt",
        choices=["json", "csv"],
        default="json",
        help="Output format (default: json).",
    )
    p.add_argument(
        "--limit",
        type=int,
        default=1000,
        help="Maximum number of results to export (default: 1000).",
    )
    p.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Write output to this file instead of stdout.",
    )
    p.add_argument(
        "--db",
        default="pulsemon.db",
        help="Path to the SQLite database file (default: pulsemon.db).",
    )
    p.set_defaults(func=handle_export)


def handle_export(args: argparse.Namespace) -> int:
    """Execute the export command and return an exit code."""
    conn = get_connection(args.db)
    init_db(conn)

    try:
        output = export_monitor_history(
            conn,
            monitor_id=args.monitor_id,
            fmt=args.fmt,
            limit=args.limit,
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    finally:
        conn.close()

    if args.output:
        args.output.write_text(output, encoding="utf-8")
        print(f"Exported to {args.output}")
    else:
        print(output)

    return 0
