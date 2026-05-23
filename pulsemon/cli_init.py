"""CLI subcommand: init — initialise the SQLite database."""
from __future__ import annotations

import argparse
import os
import sys

from pulsemon.db import init_db, get_connection


def add_init_parser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    """Register the `init` subcommand."""
    parser = subparsers.add_parser(
        "init",
        help="Initialise the pulsemon database (creates tables if they don't exist).",
    )
    parser.add_argument(
        "--db",
        default=None,
        metavar="PATH",
        help="Path to the SQLite database file (default: pulsemon.db).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Delete and recreate the database file if it already exists.",
    )
    parser.set_defaults(command="init")


def handle_init(args: argparse.Namespace) -> None:
    """Execute the `init` subcommand."""
    db_path: str = args.db or os.environ.get("PULSEMON_DB", "pulsemon.db")

    if args.force and os.path.exists(db_path):
        try:
            os.remove(db_path)
            print(f"Removed existing database: {db_path}")
        except OSError as exc:
            print(f"Error removing {db_path}: {exc}", file=sys.stderr)
            sys.exit(1)

    already_exists = os.path.exists(db_path)

    try:
        conn = get_connection(db_path)
        init_db(conn)
        conn.close()
    except Exception as exc:  # noqa: BLE001
        print(f"Failed to initialise database: {exc}", file=sys.stderr)
        sys.exit(1)

    if already_exists:
        print(f"Database already initialised (no changes made): {db_path}")
    else:
        print(f"Database initialised successfully: {db_path}")
