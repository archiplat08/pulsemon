"""CLI subcommand for tagging monitors."""
from __future__ import annotations

import argparse
import json

from pulsemon.db import get_connection
from pulsemon.monitors import get_monitor
from pulsemon.tags import add_tag, remove_tag, list_tags


def add_tag_parser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    parser = subparsers.add_parser("tag", help="Manage monitor tags")
    parser.add_argument("--db", default="pulsemon.db", help="Path to SQLite database")
    parser.add_argument("--format", choices=["text", "json"], default="text")

    sub = parser.add_subparsers(dest="tag_action", required=True)

    add_p = sub.add_parser("add", help="Add a tag to a monitor")
    add_p.add_argument("monitor_id", type=int)
    add_p.add_argument("tag")

    rm_p = sub.add_parser("remove", help="Remove a tag from a monitor")
    rm_p.add_argument("monitor_id", type=int)
    rm_p.add_argument("tag")

    list_p = sub.add_parser("list", help="List tags for a monitor")
    list_p.add_argument("monitor_id", type=int)


def handle_tag(args: argparse.Namespace, out=None) -> None:
    import sys
    if out is None:
        out = sys.stdout

    conn = get_connection(args.db)
    monitor = get_monitor(conn, args.monitor_id)
    if monitor is None:
        print(f"Monitor {args.monitor_id} not found.", file=out)
        return

    if args.tag_action == "add":
        add_tag(conn, args.monitor_id, args.tag)
        if args.format == "json":
            print(json.dumps({"status": "added", "tag": args.tag}), file=out)
        else:
            print(f"Tag '{args.tag}' added to monitor {args.monitor_id}.", file=out)

    elif args.tag_action == "remove":
        removed = remove_tag(conn, args.monitor_id, args.tag)
        if args.format == "json":
            print(json.dumps({"status": "removed" if removed else "not_found", "tag": args.tag}), file=out)
        else:
            if removed:
                print(f"Tag '{args.tag}' removed from monitor {args.monitor_id}.", file=out)
            else:
                print(f"Tag '{args.tag}' not found on monitor {args.monitor_id}.", file=out)

    elif args.tag_action == "list":
        tags = list_tags(conn, args.monitor_id)
        if args.format == "json":
            print(json.dumps({"monitor_id": args.monitor_id, "tags": tags}), file=out)
        else:
            if tags:
                print(f"Tags for monitor {args.monitor_id}: {', '.join(tags)}", file=out)
            else:
                print(f"No tags for monitor {args.monitor_id}.", file=out)
