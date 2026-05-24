"""CLI subcommand: import monitors from a JSON file."""
from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from pulsemon.db import get_connection
from pulsemon.monitors import create_monitor
from pulsemon.models import Monitor


def add_import_parser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser(
        "import",
        help="Import monitors from a JSON file exported by pulsemon.",
    )
    p.add_argument(
        "file",
        nargs="?",
        default="-",
        help="Path to JSON file (default: stdin).",
    )
    p.add_argument(
        "--db",
        default="pulsemon.db",
        help="Path to the SQLite database (default: pulsemon.db).",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse and validate without writing to the database.",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text).",
    )


def handle_import(args: argparse.Namespace) -> None:
    if args.file == "-":
        raw = sys.stdin.read()
    else:
        try:
            with open(args.file, "r", encoding="utf-8") as fh:
                raw = fh.read()
        except FileNotFoundError:
            print(f"error: file not found: {args.file}", file=sys.stderr)
            sys.exit(1)

    try:
        data: Any = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"error: invalid JSON — {exc}", file=sys.stderr)
        sys.exit(1)

    if not isinstance(data, list):
        print("error: expected a JSON array of monitor objects.", file=sys.stderr)
        sys.exit(1)

    imported, skipped = [], []
    with get_connection(args.db) as conn:
        for entry in data:
            try:
                m = Monitor(
                    id=None,
                    name=entry["name"],
                    url=entry["url"],
                    interval=int(entry.get("interval", 60)),
                    timeout=int(entry.get("timeout", 10)),
                    tag=entry.get("tag") or None,
                )
            except (KeyError, TypeError, ValueError) as exc:
                skipped.append({"entry": entry, "reason": str(exc)})
                continue

            if not args.dry_run:
                create_monitor(conn, m)
            imported.append(m)

    if args.format == "json":
        print(json.dumps({"imported": len(imported), "skipped": len(skipped)}))
    else:
        print(f"Imported {len(imported)} monitor(s), skipped {len(skipped)}.")
        for s in skipped:
            print(f"  skipped: {s['entry']} — {s['reason']}", file=sys.stderr)
