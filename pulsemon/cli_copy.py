"""CLI handler for copying (cloning) an existing monitor."""
from __future__ import annotations

import argparse

from pulsemon.db import get_connection
from pulsemon.monitors import get_monitor, create_monitor
from pulsemon.models import Monitor


def add_copy_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("copy", help="Clone an existing monitor with a new name")
    p.add_argument("monitor_id", type=int, help="ID of the monitor to copy")
    p.add_argument("new_name", help="Name for the cloned monitor")
    p.add_argument("--new-url", dest="new_url", default=None, help="Override URL for the clone")
    p.add_argument("--db", default="pulsemon.db", help="Path to SQLite database")
    p.add_argument("--json", dest="json_fmt", action="store_true", help="Output as JSON")


def handle_copy(args: argparse.Namespace) -> None:
    import json

    with get_connection(args.db) as conn:
        source = get_monitor(conn, args.monitor_id)
        if source is None:
            print(f"Error: monitor {args.monitor_id} not found.")
            return

        cloned = Monitor(
            id=None,
            name=args.new_name,
            url=args.new_url if args.new_url else source.url,
            interval=source.interval,
            timeout=source.timeout,
            tags=source.tags,
        )

        try:
            created = create_monitor(conn, cloned)
        except ValueError as exc:
            print(f"Error: {exc}")
            return

    if args.json_fmt:
        print(
            json.dumps(
                {
                    "source_id": source.id,
                    "new_id": created.id,
                    "name": created.name,
                    "url": created.url,
                    "interval": created.interval,
                    "timeout": created.timeout,
                    "tags": created.tags,
                },
                indent=2,
            )
        )
    else:
        print(
            f"Copied monitor #{source.id} '{source.name}' "
            f"-> #{created.id} '{created.name}' ({created.url})"
        )
