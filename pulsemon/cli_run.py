"""CLI handler for the 'run' subcommand — starts the scheduler loop."""
from __future__ import annotations

import argparse
import logging
import signal
import sys

from pulsemon.config import Config, load_config
from pulsemon.db import init_db
from pulsemon.scheduler import Scheduler

logger = logging.getLogger(__name__)


def add_run_parser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    """Register the 'run' subcommand on *subparsers*."""
    parser = subparsers.add_parser(
        "run",
        help="Start the uptime-monitor scheduler loop.",
    )
    parser.add_argument(
        "--config",
        default="pulsemon.toml",
        metavar="FILE",
        help="Path to TOML config file (default: pulsemon.toml).",
    )
    parser.add_argument(
        "--db",
        default=None,
        metavar="PATH",
        help="Override the SQLite database path from config.",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run a single check cycle then exit (useful for testing).",
    )


def handle_run(args: argparse.Namespace) -> None:
    """Entry point for the 'run' subcommand."""
    cfg: Config = load_config(args.config)

    db_path: str = args.db if args.db else cfg.db_path
    init_db(db_path)

    scheduler = Scheduler(db_path=db_path, config=cfg)

    if args.once:
        logger.info("Running a single check cycle.")
        scheduler.run_once()
        return

    # Graceful shutdown on SIGINT / SIGTERM
    def _stop(signum, frame):  # noqa: ANN001
        logger.info("Signal %s received — stopping scheduler.", signum)
        scheduler.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, _stop)
    signal.signal(signal.SIGTERM, _stop)

    logger.info("Starting pulsemon scheduler (db=%s).", db_path)
    scheduler.start()
