"""Build summary reports for monitors."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

from pulsemon.checks import get_latest_check
from pulsemon.history import get_check_history, get_uptime_percentage
from pulsemon.models import CheckResult, Monitor
from pulsemon.monitors import list_monitors


@dataclass
class MonitorSummary:
    monitor_id: str
    name: str
    url: str
    is_up: Optional[bool]
    last_checked_at: Optional[datetime]
    uptime_24h: Optional[float]
    uptime_7d: Optional[float]
    recent_results: List[CheckResult] = field(default_factory=list)


def build_monitor_summary(
    monitor: Monitor,
    recent_limit: int = 10,
) -> MonitorSummary:
    """Return a summary for a single monitor."""
    latest = get_latest_check(monitor.id)
    return MonitorSummary(
        monitor_id=monitor.id,
        name=monitor.name,
        url=monitor.url,
        is_up=latest.is_up if latest else None,
        last_checked_at=latest.checked_at if latest else None,
        uptime_24h=get_uptime_percentage(monitor.id, window_hours=24),
        uptime_7d=get_uptime_percentage(monitor.id, window_hours=168),
        recent_results=get_check_history(monitor.id, limit=recent_limit),
    )


def build_full_report(recent_limit: int = 10) -> List[MonitorSummary]:
    """Return summaries for all monitors."""
    return [
        build_monitor_summary(m, recent_limit=recent_limit)
        for m in list_monitors()
    ]


def summary_as_dict(summary: MonitorSummary) -> Dict:
    """Serialise a MonitorSummary to a plain dict."""
    return {
        "monitor_id": summary.monitor_id,
        "name": summary.name,
        "url": summary.url,
        "is_up": summary.is_up,
        "last_checked_at": (
            summary.last_checked_at.isoformat() if summary.last_checked_at else None
        ),
        "uptime_24h": summary.uptime_24h,
        "uptime_7d": summary.uptime_7d,
        "recent_results": [
            {
                "checked_at": r.checked_at.isoformat(),
                "is_up": r.is_up,
                "status_code": r.status_code,
                "response_time_ms": r.response_time_ms,
                "error": r.error,
            }
            for r in summary.recent_results
        ],
    }
