"""CLI handler for the 'snapshot' subcommand.

Takes a point-in-time snapshot of all monitor statuses and prints
or saves a compact summary.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone

from pulsemon.db import get_connection
from pulsemon.status import get_all_statuses, status_as_dict


def add_snapshot_parser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser(
        "snapshot",
        help="Print a point-in-time snapshot of all monitor statuses.",
    )
    p.add_argument("--db", default="pulsemon.db", help="Path to SQLite database.")
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text).",
    )
    p.add_argument(
        "--out",
        default=None,
        metavar="FILE",
        help="Write output to FILE instead of stdout.",
    )


def handle_snapshot(args: argparse.Namespace, out=None) -> None:
    if out is None:
        out = sys.stdout

    conn = get_connection(args.db)
    statuses = get_all_statuses(conn)
    conn.close()

    taken_at = datetime.now(timezone.utc).isoformat()

    if args.format == "json":
        payload = {
            "taken_at": taken_at,
            "monitors": [status_as_dict(s) for s in statuses],
        }
        _write(json.dumps(payload, indent=2), args, out)
        return

    lines = [f"Snapshot taken at {taken_at}", ""]
    if not statuses:
        lines.append("No monitors found.")
    else:
        for s in statuses:
            state = "UP" if s.is_up else ("DOWN" if s.is_up is False else "UNKNOWN")
            lines.append(f"  [{state:^7}]  {s.monitor.name}  ({s.monitor.url})")
    _write("\n".join(lines), args, out)


def _write(text: str, args: argparse.Namespace, default_out) -> None:
    if getattr(args, "out", None):
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(text + "\n")
    else:
        default_out.write(text + "\n")
