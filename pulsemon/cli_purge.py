"""CLI subcommand: purge old check results from the database."""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone

from pulsemon.db import get_connection
from pulsemon.history import purge_old_results


def add_purge_parser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    """Register the 'purge' subcommand."""
    parser = subparsers.add_parser(
        "purge",
        help="Delete check results older than a given number of days.",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        metavar="N",
        help="Remove results older than N days (default: 30).",
    )
    parser.add_argument(
        "--db",
        default="pulsemon.db",
        metavar="PATH",
        help="Path to the SQLite database file.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print how many rows would be deleted without deleting them.",
    )


def handle_purge(args: argparse.Namespace) -> None:
    """Execute the purge subcommand."""
    cutoff: datetime = datetime.now(tz=timezone.utc) - timedelta(days=args.days)

    if args.dry_run:
        conn = get_connection(args.db)
        row = conn.execute(
            "SELECT COUNT(*) FROM check_results WHERE checked_at < ?",
            (cutoff.isoformat(),),
        ).fetchone()
        count: int = row[0] if row else 0
        print(f"[dry-run] Would delete {count} result(s) older than {args.days} day(s).")
        conn.close()
        return

    deleted = purge_old_results(args.db, cutoff)
    print(f"Deleted {deleted} result(s) older than {args.days} day(s).")
