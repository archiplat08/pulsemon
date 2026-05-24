"""CLI subcommand: mute / unmute alert notifications for a monitor."""
from __future__ import annotations

import argparse
import json
from typing import Any

from pulsemon.db import get_connection
from pulsemon.mute import get_mute_status, set_mute, MuteStatus


def add_mute_parser(subparsers: Any) -> None:
    p = subparsers.add_parser("mute", help="Mute or unmute alert notifications for a monitor")
    p.add_argument("monitor_id", type=int, help="Monitor ID")
    p.add_argument(
        "--unmute",
        action="store_true",
        default=False,
        help="Unmute the monitor instead of muting it",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        dest="fmt",
        help="Output format (default: text)",
    )
    p.add_argument("--db", default="pulsemon.db", help="Path to SQLite database")


def handle_mute(args: argparse.Namespace) -> None:
    conn = get_connection(args.db)
    muted = not args.unmute
    status: MuteStatus = set_mute(conn, args.monitor_id, muted=muted)
    conn.close()

    if args.fmt == "json":
        print(json.dumps({"monitor_id": status.monitor_id, "muted": status.muted}))
    else:
        state = "muted" if status.muted else "unmuted"
        print(f"Monitor {status.monitor_id} is now {state}.")
