"""Thin shim so __main__.py can import a unified 'add_all_subparsers' helper."""
from __future__ import annotations

import argparse

from pulsemon.cli_export import add_export_parser
from pulsemon.cli_monitor import add_monitor_parser
from pulsemon.cli_report import add_report_parser
from pulsemon.cli_status import add_status_parser


def add_all_subparsers(subparsers: argparse._SubParsersAction) -> None:
    """Register every CLI subcommand onto *subparsers*."""
    add_monitor_parser(subparsers)
    add_status_parser(subparsers)
    add_report_parser(subparsers)
    add_export_parser(subparsers)


def dispatch(args: argparse.Namespace, db_path: str) -> int:
    """Route parsed args to the correct handler; return exit code."""
    from pulsemon.cli_export import handle_export
    from pulsemon.cli_report import handle_report
    from pulsemon.cli_status import handle_status

    cmd = getattr(args, "cmd", None)
    if cmd == "monitor":
        from pulsemon.cli_monitor import handle_monitor
        return handle_monitor(args, db_path)
    if cmd == "status":
        return handle_status(args, db_path)
    if cmd == "report":
        return handle_report(args, db_path)
    if cmd == "export":
        return handle_export(args, db_path)
    return 0
