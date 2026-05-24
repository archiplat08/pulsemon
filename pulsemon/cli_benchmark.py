"""CLI handler for the benchmark subcommand."""
from __future__ import annotations

import argparse
import json
import time

from pulsemon.benchmark import run_benchmark, benchmark_as_dict
from pulsemon.db import get_connection
from pulsemon.monitors import get_monitor


def add_benchmark_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser(
        "benchmark",
        help="Run repeated checks against a monitor and report latency stats",
    )
    p.add_argument("monitor_id", type=int, help="ID of the monitor to benchmark")
    p.add_argument(
        "--runs",
        type=int,
        default=5,
        help="Number of requests to make (default: 5)",
    )
    p.add_argument(
        "--delay",
        type=float,
        default=0.5,
        help="Seconds to wait between requests (default: 0.5)",
    )
    p.add_argument(
        "--format",
        dest="fmt",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    p.add_argument("--db", default=None, help="Path to SQLite database")


def handle_benchmark(args: argparse.Namespace) -> None:
    db_path = getattr(args, "db", None)
    conn = get_connection(db_path)

    monitor = get_monitor(conn, args.monitor_id)
    if monitor is None:
        print(f"Monitor {args.monitor_id} not found.")
        return

    print(f"Benchmarking '{monitor.name}' with {args.runs} runs...")
    result = run_benchmark(monitor, runs=args.runs, delay=args.delay)

    if args.fmt == "json":
        print(json.dumps(benchmark_as_dict(result), indent=2))
    else:
        d = benchmark_as_dict(result)
        print(f"  URL       : {d['url']}")
        print(f"  Runs      : {d['runs']}")
        print(f"  Successful: {d['successful']}")
        print(f"  Failed    : {d['failed']}")
        print(f"  Min (ms)  : {d['min_ms']}")
        print(f"  Max (ms)  : {d['max_ms']}")
        print(f"  Avg (ms)  : {d['avg_ms']}")
        print(f"  P95 (ms)  : {d['p95_ms']}")
