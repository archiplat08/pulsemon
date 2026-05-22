"""Export monitor check history to CSV or JSON formats."""

from __future__ import annotations

import csv
import io
import json
from typing import Literal

from pulsemon.checks import list_check_results
from pulsemon.models import CheckResult

ExportFormat = Literal["csv", "json"]


def _result_to_dict(result: CheckResult) -> dict:
    return {
        "monitor_id": result.monitor_id,
        "checked_at": result.checked_at,
        "status": result.status,
        "response_time_ms": result.response_time_ms,
        "status_code": result.status_code,
        "error": result.error,
    }


def export_to_json(conn, monitor_id: int, limit: int = 1000) -> str:
    """Return check results for a monitor as a JSON string."""
    results = list_check_results(conn, monitor_id, limit=limit)
    data = [_result_to_dict(r) for r in results]
    return json.dumps(data, indent=2, default=str)


def export_to_csv(conn, monitor_id: int, limit: int = 1000) -> str:
    """Return check results for a monitor as a CSV string."""
    results = list_check_results(conn, monitor_id, limit=limit)
    fieldnames = ["monitor_id", "checked_at", "status", "response_time_ms", "status_code", "error"]

    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fieldnames)
    writer.writeheader()
    for r in results:
        writer.writerow(_result_to_dict(r))
    return buf.getvalue()


def export_monitor_history(conn, monitor_id: int, fmt: ExportFormat = "json", limit: int = 1000) -> str:
    """Export monitor history in the requested format.

    Args:
        conn: Database connection.
        monitor_id: ID of the monitor to export.
        fmt: Output format, either ``"json"`` or ``"csv"``.
        limit: Maximum number of results to include.

    Returns:
        Serialised string in the requested format.

    Raises:
        ValueError: If an unsupported format is requested.
    """
    if fmt == "json":
        return export_to_json(conn, monitor_id, limit=limit)
    if fmt == "csv":
        return export_to_csv(conn, monitor_id, limit=limit)
    raise ValueError(f"Unsupported export format: {fmt!r}. Choose 'json' or 'csv'.")
