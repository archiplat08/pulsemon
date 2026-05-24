"""Benchmark a monitor by running repeated HTTP checks and collecting latency stats."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import List, Optional

import requests

from pulsemon.models import Monitor


@dataclass
class BenchmarkResult:
    monitor_id: int
    url: str
    runs: int
    latencies_ms: List[float] = field(default_factory=list)
    failed: int = 0

    @property
    def successful(self) -> int:
        return len(self.latencies_ms)

    @property
    def min_ms(self) -> Optional[float]:
        return round(min(self.latencies_ms), 2) if self.latencies_ms else None

    @property
    def max_ms(self) -> Optional[float]:
        return round(max(self.latencies_ms), 2) if self.latencies_ms else None

    @property
    def avg_ms(self) -> Optional[float]:
        if not self.latencies_ms:
            return None
        return round(sum(self.latencies_ms) / len(self.latencies_ms), 2)

    @property
    def p95_ms(self) -> Optional[float]:
        if not self.latencies_ms:
            return None
        sorted_lat = sorted(self.latencies_ms)
        idx = max(0, int(len(sorted_lat) * 0.95) - 1)
        return round(sorted_lat[idx], 2)


def run_benchmark(
    monitor: Monitor,
    runs: int = 5,
    delay: float = 0.5,
) -> BenchmarkResult:
    result = BenchmarkResult(
        monitor_id=monitor.id,  # type: ignore[arg-type]
        url=monitor.url,
        runs=runs,
    )
    for i in range(runs):
        try:
            start = time.perf_counter()
            resp = requests.get(monitor.url, timeout=monitor.timeout)
            elapsed_ms = (time.perf_counter() - start) * 1000
            if resp.status_code < 500:
                result.latencies_ms.append(elapsed_ms)
            else:
                result.failed += 1
        except Exception:
            result.failed += 1
        if i < runs - 1 and delay > 0:
            time.sleep(delay)
    return result


def benchmark_as_dict(result: BenchmarkResult) -> dict:
    return {
        "monitor_id": result.monitor_id,
        "url": result.url,
        "runs": result.runs,
        "successful": result.successful,
        "failed": result.failed,
        "min_ms": result.min_ms,
        "max_ms": result.max_ms,
        "avg_ms": result.avg_ms,
        "p95_ms": result.p95_ms,
    }
