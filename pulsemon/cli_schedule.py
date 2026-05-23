"""CLI subcommand: schedule — show next expected check times for monitors."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone

from pulsemon.db import get_connection
from pulsemon.monitors import list_monitors
from pulsemon.checks import get_latest_check


def add_schedule_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("schedule", help="Show next scheduled check times")
    p.add_argument("--db", default="pulsemon.db", help="Path to SQLite database")
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )


def handle_schedule(args: argparse.Namespace, out=None) -> None:
    import sys

    if out is None:
        out = sys.stdout

    conn = get_connection(args.db)
    monitors = list_monitors(conn)
    conn.close()

    rows = []
    now = datetime.now(tz=timezone.utc)
    for m in monitors:
        conn = get_connection(args.db)
        latest = get_latest_check(conn, m.id)
        conn.close()

        if latest is None:
            next_check = now
            seconds_until = 0
        else:
            from datetime import timedelta

            next_check = latest.checked_at + timedelta(seconds=m.interval)
            delta = (next_check - now).total_seconds()
            seconds_until = max(0, int(delta))

        rows.append(
            {
                "id": m.id,
                "name": m.name,
                "url": m.url,
                "interval": m.interval,
                "next_check": next_check.isoformat(),
                "seconds_until": seconds_until,
            }
        )

    if args.format == "json":
        out.write(json.dumps(rows, indent=2))
        out.write("\n")
    else:
        if not rows:
            out.write("No monitors configured.\n")
            return
        out.write(f"{'ID':<6} {'Name':<24} {'Interval':>10} {'Next Check (UTC)':<28} {'In (s)':>8}\n")
        out.write("-" * 82 + "\n")
        for r in rows:
            out.write(
                f"{r['id']:<6} {r['name']:<24} {r['interval']:>10} "
                f"{r['next_check']:<28} {r['seconds_until']:>8}\n"
            )
