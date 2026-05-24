"""CLI handler for the digest command — periodic summary digest output."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone

from pulsemon.db import get_connection
from pulsemon.digest import build_digest, digest_as_dict


def add_digest_parser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser("digest", help="Print a summary digest of all monitors")
    p.add_argument("--db", default="pulsemon.db", help="Path to SQLite database")
    p.add_argument(
        "--hours",
        type=int,
        default=24,
        help="Look-back window in hours (default: 24)",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    p.set_defaults(command="digest")


def handle_digest(args: argparse.Namespace, out=sys.stdout) -> int:
    conn = get_connection(args.db)
    digest = build_digest(conn, hours=args.hours)
    conn.close()

    if args.format == "json":
        out.write(json.dumps(digest_as_dict(digest), indent=2))
        out.write("\n")
        return 0

    # text output
    out.write(
        f"Digest ({args.hours}h window) — generated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')} UTC\n"
    )
    out.write(f"  Monitors total : {digest.total}\n")
    out.write(f"  Currently UP   : {digest.up}\n")
    out.write(f"  Currently DOWN : {digest.down}\n")
    out.write(f"  No data        : {digest.no_data}\n")
    out.write(f"  Checks in window: {digest.checks_in_window}\n")
    out.write(f"  Avg uptime     : {digest.avg_uptime_pct:.1f}%\n")
    if digest.incidents_opened:
        out.write(f"  Incidents opened: {digest.incidents_opened}\n")
    return 0
