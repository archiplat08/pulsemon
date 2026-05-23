"""Register all CLI subparsers and dispatch to handlers."""
from __future__ import annotations

import argparse

from pulsemon.cli_check import add_check_parser, handle_check
from pulsemon.cli_export import add_export_parser, handle_export
from pulsemon.cli_history import add_history_parser, handle_history
from pulsemon.cli_monitor import add_monitor_parser, handle_monitor
from pulsemon.cli_notify import add_notify_parser, handle_notify
from pulsemon.cli_report import add_report_parser, handle_report
from pulsemon.cli_status import add_status_parser, handle_status

_REGISTRY = [
    ("monitor", add_monitor_parser, handle_monitor),
    ("status", add_status_parser, handle_status),
    ("report", add_report_parser, handle_report),
    ("export", add_export_parser, handle_export),
    ("history", add_history_parser, handle_history),
    ("notify", add_notify_parser, handle_notify),
    ("check", add_check_parser, handle_check),
]


def add_all_subparsers(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    """Attach every subcommand to *subparsers*."""
    for _name, adder, _handler in _REGISTRY:
        adder(subparsers)


def dispatch(args: argparse.Namespace, db_path: str) -> None:
    """Route *args* to the correct subcommand handler."""
    handlers = {name: handler for name, _, handler in _REGISTRY}
    handler = handlers.get(args.command)
    if handler is None:
        raise ValueError(f"Unknown command: {args.command!r}")
    handler(args, db_path)
