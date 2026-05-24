"""Register all CLI subparsers and dispatch to the correct handler."""
from __future__ import annotations

import argparse

from pulsemon.cli_check import add_check_parser, handle_check
from pulsemon.cli_config import add_config_parser, handle_config
from pulsemon.cli_export import add_export_parser, handle_export
from pulsemon.cli_history import add_history_parser, handle_history
from pulsemon.cli_init import add_init_parser, handle_init
from pulsemon.cli_monitor import add_monitor_parser, handle_monitor
from pulsemon.cli_notify import add_notify_parser, handle_notify
from pulsemon.cli_ping import add_ping_parser, handle_ping
from pulsemon.cli_purge import add_purge_parser, handle_purge
from pulsemon.cli_report import add_report_parser, handle_report
from pulsemon.cli_reset import add_reset_parser, handle_reset
from pulsemon.cli_run import add_run_parser, handle_run
from pulsemon.cli_schedule import add_schedule_parser, handle_schedule
from pulsemon.cli_status import add_status_parser, handle_status
from pulsemon.cli_version import add_version_parser, handle_version

_REGISTRY = [
    ("check", add_check_parser, handle_check),
    ("config", add_config_parser, handle_config),
    ("export", add_export_parser, handle_export),
    ("history", add_history_parser, handle_history),
    ("init", add_init_parser, handle_init),
    ("monitor", add_monitor_parser, handle_monitor),
    ("notify", add_notify_parser, handle_notify),
    ("ping", add_ping_parser, handle_ping),
    ("purge", add_purge_parser, handle_purge),
    ("report", add_report_parser, handle_report),
    ("reset", add_reset_parser, handle_reset),
    ("run", add_run_parser, handle_run),
    ("schedule", add_schedule_parser, handle_schedule),
    ("status", add_status_parser, handle_status),
    ("version", add_version_parser, handle_version),
]


def add_all_subparsers(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    """Attach every subcommand to *subparsers*."""
    for _name, add_fn, _handler in _REGISTRY:
        add_fn(subparsers)


def dispatch(args: argparse.Namespace) -> int:
    """Call the handler that matches *args.command*; return an exit code."""
    for name, _add_fn, handler in _REGISTRY:
        if args.command == name:
            return handler(args) or 0
    return 0
