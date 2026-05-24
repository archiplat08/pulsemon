"""Response-time statistics for a single monitor."""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Any


@dataclass
class MonitorStats:
    monitor_id: int
    sample_size: int
    min_ms: float
    max_ms: float
    avg_ms: float
    p95_ms: float
    p99_ms: float
    error_rate: float  # 0.0 – 1.0


def get_monitor_stats(
    conn: sqlite3.Connection,
    monitor_id: int,
    *,
    limit: int = 100,
) -> MonitorStats:
    """Compute latency statistics from the most recent *limit* check results."""
    rows = conn.execute(
        """
        SELECT response_ms, is_up
        FROM check_results
        WHERE monitor_id = ?
        ORDER BY checked_at DESC
        LIMIT ?
        """,
        (monitor_id, limit),
    ).fetchall()

    if not rows:
        return MonitorStats(
            monitor_id=monitor_id,
            sample_size=0,
            min_ms=0.0,
            max_ms=0.0,
            avg_ms=0.0,
            p95_ms=0.0,
            p99_ms=0.0,
            error_rate=0.0,
        )

    latencies = sorted(
        row["response_ms"] for row in rows if row["response_ms"] is not None
    )
    total = len(rows)
    errors = sum(1 for row in rows if not row["is_up"])

    def _percentile(data: list[float], pct: float) -> float:
        if not data:
            return 0.0
        idx = int(len(data) * pct / 100)
        idx = min(idx, len(data) - 1)
        return data[idx]

    return MonitorStats(
        monitor_id=monitor_id,
        sample_size=total,
        min_ms=latencies[0] if latencies else 0.0,
        max_ms=latencies[-1] if latencies else 0.0,
        avg_ms=sum(latencies) / len(latencies) if latencies else 0.0,
        p95_ms=_percentile(latencies, 95),
        p99_ms=_percentile(latencies, 99),
        error_rate=errors / total,
    )


def stats_as_dict(stats: MonitorStats) -> dict[str, Any]:
    return {
        "monitor_id": stats.monitor_id,
        "sample_size": stats.sample_size,
        "min_ms": round(stats.min_ms, 3),
        "max_ms": round(stats.max_ms, 3),
        "avg_ms": round(stats.avg_ms, 3),
        "p95_ms": round(stats.p95_ms, 3),
        "p99_ms": round(stats.p99_ms, 3),
        "error_rate": round(stats.error_rate, 4),
    }
