"""CLI subcommand: search monitors by name, URL, or tag."""
from __future__ import annotations

import argparse
import json

from pulsemon.db import get_connection
from pulsemon.search import search_monitors, search_result_as_dict


def add_search_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("search", help="Search monitors by name, URL, or tag")
    p.add_argument("query", help="Search term")
    p.add_argument(
        "--field",
        choices=["name", "url", "tag", "any"],
        default="any",
        help="Field to search in (default: any)",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        dest="fmt",
        help="Output format (default: text)",
    )
    p.add_argument("--db", default="pulsemon.db", help="Path to SQLite database")
    p.set_defaults(handler=handle_search)


def handle_search(args: argparse.Namespace) -> None:
    conn = get_connection(args.db)
    results = search_monitors(conn, args.query, field=args.field)
    conn.close()

    if args.fmt == "json":
        print(json.dumps([search_result_as_dict(r) for r in results], indent=2))
        return

    if not results:
        print(f"No monitors matched '{args.query}'.")
        return

    print(f"Found {len(results)} monitor(s) matching '{args.query}':")
    for m in results:
        tag_str = f"  tags={m.tags}" if m.tags else ""
        print(f"  [{m.id}] {m.name} — {m.url}{tag_str}")
