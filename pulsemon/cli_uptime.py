"""CLI handler for uptime reporting across monitors."""
from __future__ import annotations

import argparse
import json

from pulsemon.db import get_connection
from pulsemon.monitors import list_monitors
from pulsemon.history import get_uptime_percentage


def add_uptime_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("uptime", help="Show uptime percentages for monitors")
    p.add_argument("--db", default="pulsemon.db", help="Path to SQLite database")
    p.add_argument(
        "--days",
        type=int,
        default=30,
        help="Number of days to calculate uptime over (default: 30)",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        dest="fmt",
        help="Output format",
    )
    p.add_argument(
        "--min-uptime",
        type=float,
        default=None,
        dest="min_uptime",
        help="Only show monitors below this uptime percentage",
    )


def handle_uptime(args: argparse.Namespace) -> None:
    conn = get_connection(args.db)
    monitors = list_monitors(conn)

    rows = []
    for m in monitors:
        pct = get_uptime_percentage(conn, m.id, days=args.days)
        rows.append({"id": m.id, "name": m.name, "url": m.url, "uptime": pct})

    if args.min_uptime is not None:
        rows = [
            r for r in rows
            if r["uptime"] is None or r["uptime"] < args.min_uptime
        ]

    conn.close()

    if args.fmt == "json":
        print(json.dumps(rows, indent=2))
        return

    if not rows:
        print("No monitors found.")
        return

    print(f"{'ID':<6} {'Name':<30} {'Uptime':>10}  URL")
    print("-" * 70)
    for r in rows:
        pct_str = f"{r['uptime']:.1f}%" if r["uptime"] is not None else "N/A"
        print(f"{r['id']:<6} {r['name']:<30} {pct_str:>10}  {r['url']}")
