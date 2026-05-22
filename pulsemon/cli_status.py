"""CLI sub-command: pulsemon status"""
from __future__ import annotations

import json
import sys

from pulsemon.db import get_connection, init_db
from pulsemon.status import get_all_statuses, get_monitor_status, status_as_dict


def add_status_parser(subparsers):
    """Register the 'status' sub-command on *subparsers*."""
    p = subparsers.add_parser("status", help="Show current monitor statuses")
    p.add_argument(
        "--db",
        default="pulsemon.db",
        help="Path to the SQLite database file (default: pulsemon.db)",
    )
    p.add_argument(
        "--monitor-id",
        default=None,
        help="Show status for a single monitor by ID",
    )
    p.add_argument(
        "--format",
        choices=["json", "text"],
        default="text",
        help="Output format (default: text)",
    )
    p.set_defaults(func=handle_status)
    return p


def handle_status(args, out=None):
    """Execute the status sub-command."""
    if out is None:
        out = sys.stdout

    conn = get_connection(args.db)
    init_db(conn)

    if args.monitor_id:
        status = get_monitor_status(conn, args.monitor_id)
        if status is None:
            print(f"Monitor '{args.monitor_id}' not found.", file=sys.stderr)
            sys.exit(1)
        statuses = [status]
    else:
        statuses = get_all_statuses(conn)

    if args.format == "json":
        data = [status_as_dict(s) for s in statuses]
        json.dump(data, out, indent=2)
        out.write("\n")
    else:
        if not statuses:
            print("No monitors configured.", file=out)
            return
        for s in statuses:
            up_label = "UP" if s.is_up else ("DOWN" if s.is_up is False else "UNKNOWN")
            uptime = f"{s.uptime_24h:.1f}%" if s.uptime_24h is not None else "n/a"
            print(
                f"[{up_label:>7}] {s.name} ({s.url})  "
                f"uptime_24h={uptime}  "
                f"last_code={s.last_status_code or 'n/a'}  "
                f"response={s.last_response_ms or 'n/a'}ms",
                file=out,
            )
