"""CLI subcommand: config — show or validate the current configuration."""

from __future__ import annotations

import argparse
import json
import sys

from pulsemon.config import Config, load_config


def add_config_parser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    """Register the 'config' subcommand."""
    parser = subparsers.add_parser(
        "config",
        help="Show or validate the current pulsemon configuration.",
    )
    parser.add_argument(
        "--config",
        metavar="FILE",
        default=None,
        help="Path to a TOML config file (default: pulsemon.toml).",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text).",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Exit with code 0 if config is valid, 1 otherwise.",
    )


def handle_config(args: argparse.Namespace, out=sys.stdout) -> int:
    """Handle the 'config' subcommand.  Returns an exit code."""
    try:
        cfg: Config = load_config(args.config)
    except Exception as exc:  # noqa: BLE001
        if getattr(args, "validate", False):
            print(f"Invalid configuration: {exc}", file=sys.stderr)
            return 1
        print(f"Error loading configuration: {exc}", file=sys.stderr)
        return 1

    if getattr(args, "validate", False):
        print("Configuration is valid.", file=out)
        return 0

    fmt = getattr(args, "format", "text")
    if fmt == "json":
        data = {
            "db_path": cfg.db_path,
            "check_interval": cfg.check_interval,
            "log_level": cfg.log_level,
            "alert": cfg.alert.as_dict(),
        }
        print(json.dumps(data, indent=2), file=out)
    else:
        print(f"db_path        : {cfg.db_path}", file=out)
        print(f"check_interval : {cfg.check_interval}s", file=out)
        print(f"log_level      : {cfg.log_level}", file=out)
        print(f"alert.webhook  : {cfg.alert.webhook_url or '(none)'}", file=out)
        print(f"alert.email    : {cfg.alert.email_to or '(none)'}", file=out)

    return 0
