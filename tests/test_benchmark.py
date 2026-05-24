"""Unit tests for pulsemon.benchmark."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from pulsemon.benchmark import BenchmarkResult, benchmark_as_dict, run_benchmark
from pulsemon.models import Monitor


@pytest.fixture()
def monitor() -> Monitor:
    return Monitor(
        id=1,
        name="Test",
        url="https://example.com",
        interval=60,
        timeout=5,
    )


def _fake_response(status_code: int = 200) -> MagicMock:
    r = MagicMock()
    r.status_code = status_code
    return r


def test_run_benchmark_all_success(monitor):
    with patch("pulsemon.benchmark.requests.get", return_value=_fake_response(200)):
        result = run_benchmark(monitor, runs=3, delay=0)
    assert result.successful == 3
    assert result.failed == 0
    assert len(result.latencies_ms) == 3


def test_run_benchmark_server_errors_count_as_failed(monitor):
    with patch("pulsemon.benchmark.requests.get", return_value=_fake_response(500)):
        result = run_benchmark(monitor, runs=3, delay=0)
    assert result.successful == 0
    assert result.failed == 3


def test_run_benchmark_exceptions_count_as_failed(monitor):
    with patch("pulsemon.benchmark.requests.get", side_effect=Exception("timeout")):
        result = run_benchmark(monitor, runs=4, delay=0)
    assert result.failed == 4
    assert result.successful == 0


def test_benchmark_result_stats_empty():
    r = BenchmarkResult(monitor_id=1, url="https://x.com", runs=3)
    assert r.min_ms is None
    assert r.max_ms is None
    assert r.avg_ms is None
    assert r.p95_ms is None


def test_benchmark_result_stats_computed():
    r = BenchmarkResult(monitor_id=1, url="https://x.com", runs=4)
    r.latencies_ms = [100.0, 200.0, 150.0, 300.0]
    assert r.min_ms == 100.0
    assert r.max_ms == 300.0
    assert r.avg_ms == 187.5
    assert r.p95_ms == 300.0


def test_benchmark_as_dict_shape(monitor):
    with patch("pulsemon.benchmark.requests.get", return_value=_fake_response(200)):
        result = run_benchmark(monitor, runs=2, delay=0)
    d = benchmark_as_dict(result)
    assert d["monitor_id"] == 1
    assert d["url"] == "https://example.com"
    assert d["runs"] == 2
    assert "successful" in d
    assert "failed" in d
    assert "min_ms" in d
    assert "avg_ms" in d
    assert "p95_ms" in d
