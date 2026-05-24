"""CLI handler for per-monitor response-time statistics."""
from __future__ import annotations

import argparse
import json

from pulsemon.db import get_connection
from pulsemon.monitors import get_monitor
from pulsemon.stats import get_monitor_stats, stats_as_dict


def add_stats_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("stats", help="Show response-time statistics for a monitor")
    p.add_argument("monitor_id", type=int, help="ID of the monitor")
    p.add_argument(
        "--limit",
        type=int,
        default=100,
        help="Number of recent checks to include (default: 100)",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        dest="fmt",
        help="Output format (default: text)",
    )
    p.add_argument("--db", default=None, help="Path to SQLite database")


def handle_stats(args: argparse.Namespace) -> None:
    db_path = args.db
    conn = get_connection(db_path)

    monitor = get_monitor(conn, args.monitor_id)
    if monitor is None:
        print(f"Monitor {args.monitor_id} not found.")
        return

    stats = get_monitor_stats(conn, args.monitor_id, limit=args.limit)

    if args.fmt == "json":
        print(json.dumps(stats_as_dict(stats), indent=2))
        return

    print(f"Stats for monitor #{monitor.id} — {monitor.name}")
    print(f"  Checks analysed : {stats.sample_size}")
    if stats.sample_size == 0:
        print("  No check results available.")
        return
    print(f"  Min latency     : {stats.min_ms:.1f} ms")
    print(f"  Max latency     : {stats.max_ms:.1f} ms")
    print(f"  Avg latency     : {stats.avg_ms:.1f} ms")
    print(f"  P95 latency     : {stats.p95_ms:.1f} ms")
    print(f"  P99 latency     : {stats.p99_ms:.1f} ms")
    print(f"  Error rate      : {stats.error_rate * 100:.1f} %")
