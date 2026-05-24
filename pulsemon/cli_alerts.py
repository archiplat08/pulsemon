"""CLI subcommand: alerts — list and clear stored alert history."""
from __future__ import annotations

import argparse
import json
from typing import Any

from pulsemon.alert_log import list_alert_logs, clear_alert_logs, alert_log_as_dict
from pulsemon.db import get_connection


def add_alerts_parser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser("alerts", help="Manage alert history")
    p.add_argument("--db", default="pulsemon.db", help="Path to SQLite database")
    p.add_argument("--format", choices=["text", "json"], default="text", dest="fmt")
    p.add_argument("--limit", type=int, default=50, help="Max rows to display")

    sub = p.add_subparsers(dest="alerts_cmd")
    sub.add_parser("list", help="List recent alerts")
    clear_p = sub.add_parser("clear", help="Delete all alert history")
    clear_p.add_argument("--yes", action="store_true", help="Skip confirmation")


def handle_alerts(args: argparse.Namespace) -> None:
    """Dispatch the alerts subcommand to the appropriate handler."""
    cmd = getattr(args, "alerts_cmd", None) or "list"
    conn = get_connection(args.db)
    try:
        if cmd == "list":
            _handle_list(conn, args)
        elif cmd == "clear":
            _handle_clear(conn, args)
    finally:
        conn.close()


def _handle_list(conn: Any, args: argparse.Namespace) -> None:
    logs = list_alert_logs(conn, limit=args.limit)
    if args.fmt == "json":
        print(json.dumps([alert_log_as_dict(lg) for lg in logs], indent=2))
        return
    if not logs:
        print("No alerts recorded.")
        return
    for lg in logs:
        status = "DOWN" if not lg.is_recovery else "RECOVERY"
        print(f"[{lg.sent_at}] {lg.monitor_name} — {status} via {lg.channel}")


def _handle_clear(conn: Any, args: argparse.Namespace) -> None:
    if not getattr(args, "yes", False):
        answer = input("Delete all alert history? [y/N] ").strip().lower()
        if answer != "y":
            print("Aborted.")
            return
    deleted = clear_alert_logs(conn)
    print(f"Deleted {deleted} alert log(s).")
