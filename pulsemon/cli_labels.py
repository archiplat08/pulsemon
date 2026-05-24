"""CLI subcommand: label — attach/remove/list key-value labels on monitors."""
from __future__ import annotations

import argparse
import json

from pulsemon.db import get_connection
from pulsemon.labels import get_labels, set_label, remove_label
from pulsemon.monitors import get_monitor


def add_labels_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("label", help="manage monitor labels")
    p.add_argument("monitor_id", type=int, help="monitor ID")
    p.add_argument("--set", metavar="KEY=VALUE", dest="set_kv",
                   help="set a label (e.g. env=prod)")
    p.add_argument("--remove", metavar="KEY", dest="remove_key",
                   help="remove a label by key")
    p.add_argument("--format", choices=["text", "json"], default="text")
    p.add_argument("--db", default="pulsemon.db")


def handle_labels(args: argparse.Namespace) -> None:
    conn = get_connection(args.db)
    monitor = get_monitor(conn, args.monitor_id)
    if monitor is None:
        print(f"monitor {args.monitor_id} not found")
        return

    if args.set_kv:
        if "=" not in args.set_kv:
            print("--set requires KEY=VALUE format")
            return
        key, value = args.set_kv.split("=", 1)
        set_label(conn, args.monitor_id, key.strip(), value.strip())
        print(f"label '{key.strip()}' set on monitor {args.monitor_id}")
        return

    if args.remove_key:
        remove_label(conn, args.monitor_id, args.remove_key.strip())
        print(f"label '{args.remove_key.strip()}' removed from monitor {args.monitor_id}")
        return

    labels = get_labels(conn, args.monitor_id)
    if args.format == "json":
        print(json.dumps(labels))
    else:
        if not labels:
            print(f"no labels for monitor {args.monitor_id}")
        else:
            for k, v in labels.items():
                print(f"  {k} = {v}")
