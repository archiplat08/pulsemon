"""CLI subcommand: manage retry settings for monitors."""
from __future__ import annotations

import argparse
import json

from pulsemon.db import get_connection
from pulsemon.retries import get_retry_config, set_retry_config, RetryConfig


def add_retries_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("retries", help="View or update retry settings for a monitor")
    p.add_argument("monitor_id", type=int, help="Monitor ID")
    p.add_argument("--set-max", type=int, dest="max_retries", help="Set max retry attempts (1-10)")
    p.add_argument("--set-delay", type=float, dest="retry_delay", help="Set delay between retries in seconds")
    p.add_argument("--format", choices=["text", "json"], default="text")
    p.add_argument("--db", default="pulsemon.db")


def handle_retries(args: argparse.Namespace) -> None:
    conn = get_connection(args.db)
    monitor_id: int = args.monitor_id

    if args.max_retries is not None or args.retry_delay is not None:
        current = get_retry_config(conn, monitor_id)
        new_max = args.max_retries if args.max_retries is not None else current.max_retries
        new_delay = args.retry_delay if args.retry_delay is not None else current.retry_delay
        cfg = set_retry_config(conn, monitor_id, max_retries=new_max, retry_delay=new_delay)
        if getattr(args, "format", "text") == "json":
            print(json.dumps({"monitor_id": monitor_id, "max_retries": cfg.max_retries, "retry_delay": cfg.retry_delay}))
        else:
            print(f"Retry config updated for monitor {monitor_id}: max_retries={cfg.max_retries}, retry_delay={cfg.retry_delay}s")
    else:
        cfg = get_retry_config(conn, monitor_id)
        if getattr(args, "format", "text") == "json":
            print(json.dumps({"monitor_id": monitor_id, "max_retries": cfg.max_retries, "retry_delay": cfg.retry_delay}))
        else:
            print(f"Monitor {monitor_id} retry config: max_retries={cfg.max_retries}, retry_delay={cfg.retry_delay}s")
