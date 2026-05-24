"""CLI handler for listing and managing downtime incidents."""
from __future__ import annotations

import argparse
import json
from typing import Any

from pulsemon.db import get_connection
from pulsemon.incidents import list_incidents, resolve_incident, incident_as_dict


def add_incidents_parser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser("incidents", help="List or resolve downtime incidents")
    sub = p.add_subparsers(dest="incidents_cmd")

    ls = sub.add_parser("list", help="List recorded incidents")
    ls.add_argument("--monitor-id", type=int, default=None, help="Filter by monitor ID")
    ls.add_argument("--open", action="store_true", dest="open_only", help="Show only unresolved incidents")
    ls.add_argument("--format", choices=["text", "json"], default="text")
    ls.add_argument("--db", default="pulsemon.db")

    rs = sub.add_parser("resolve", help="Mark an incident as resolved")
    rs.add_argument("incident_id", type=int)
    rs.add_argument("--db", default="pulsemon.db")


def handle_incidents(args: argparse.Namespace, out: Any = None) -> None:
    import sys
    out = out or sys.stdout

    cmd = getattr(args, "incidents_cmd", None)
    if cmd == "resolve":
        conn = get_connection(args.db)
        resolve_incident(conn, args.incident_id)
        out.write(f"Incident {args.incident_id} marked as resolved.\n")
        return

    # default: list
    conn = get_connection(getattr(args, "db", "pulsemon.db"))
    monitor_id = getattr(args, "monitor_id", None)
    open_only = getattr(args, "open_only", False)
    fmt = getattr(args, "format", "text")

    incidents = list_incidents(conn, monitor_id=monitor_id, open_only=open_only)

    if fmt == "json":
        out.write(json.dumps([incident_as_dict(i) for i in incidents], indent=2))
        out.write("\n")
        return

    if not incidents:
        out.write("No incidents found.\n")
        return

    for inc in incidents:
        status = "OPEN" if inc.resolved_at is None else "RESOLVED"
        out.write(
            f"[{inc.id}] monitor={inc.monitor_id} started={inc.started_at} "
            f"resolved={inc.resolved_at or '-'} status={status}\n"
        )
