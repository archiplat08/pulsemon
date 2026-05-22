"""Entry point: `python -m pulsemon` starts the scheduler."""

import argparse
import logging
import signal
import sys

from pulsemon.config import load_config
from pulsemon.db import db_conn, init_db
from pulsemon.scheduler import Scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger("pulsemon")


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="pulsemon",
        description="Minimal self-hosted uptime monitor",
    )
    parser.add_argument(
        "--config",
        default=None,
        metavar="PATH",
        help="Path to pulsemon.toml (default: pulsemon.toml)",
    )
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    cfg = load_config(args.config)

    logger.info("initialising database at %s", cfg.db_path)
    with db_conn(cfg.db_path) as conn:
        init_db(conn)

    alert_config = cfg.alerts.as_dict() or None
    scheduler = Scheduler(
        db_path=cfg.db_path,
        tick_seconds=cfg.tick_seconds,
        alert_config=alert_config,
    )

    stop_signals = (signal.SIGINT, signal.SIGTERM)

    def _handle_signal(sig, frame):  # pragma: no cover
        logger.info("received signal %s, shutting down …", signal.Signals(sig).name)
        scheduler.stop()
        sys.exit(0)

    for sig in stop_signals:  # pragma: no cover
        signal.signal(sig, _handle_signal)

    logger.info(
        "pulsemon started — tick=%ds db=%s",
        cfg.tick_seconds,
        cfg.db_path,
    )
    scheduler.start()
    scheduler._thread.join()  # type: ignore[union-attr]
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
