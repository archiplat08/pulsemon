"""Tests for pulsemon.cli_benchmark."""
from __future__ import annotations

import argparse
import json
from unittest.mock import MagicMock, patch

import pytest

from pulsemon.benchmark import BenchmarkResult
from pulsemon.cli_benchmark import add_benchmark_parser, handle_benchmark
from pulsemon.models import Monitor


@pytest.fixture()
def _build_parser():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="command")
    add_benchmark_parser(sub)
    return p


def _make_args(**kwargs):
    defaults = {
        "monitor_id": 1,
        "runs": 3,
        "delay": 0.0,
        "fmt": "text",
        "db": None,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


@pytest.fixture()
def _monitor():
    return Monitor(id=1, name="Demo", url="https://example.com", interval=60, timeout=5)


@pytest.fixture()
def _bench_result(_monitor):
    r = BenchmarkResult(monitor_id=1, url=_monitor.url, runs=3)
    r.latencies_ms = [120.0, 130.0, 125.0]
    return r


def test_add_benchmark_parser_registers_command(_build_parser):
    args = _build_parser.parse_args(["benchmark", "1"])
    assert args.command == "benchmark"


def test_add_benchmark_parser_defaults(_build_parser):
    args = _build_parser.parse_args(["benchmark", "7"])
    assert args.runs == 5
    assert args.delay == 0.5
    assert args.fmt == "text"


def test_handle_benchmark_monitor_not_found(capsys):
    with patch("pulsemon.cli_benchmark.get_connection"), \
         patch("pulsemon.cli_benchmark.get_monitor", return_value=None):
        handle_benchmark(_make_args(monitor_id=99))
    out = capsys.readouterr().out
    assert "not found" in out


def test_handle_benchmark_text_output(capsys, _monitor, _bench_result):
    with patch("pulsemon.cli_benchmark.get_connection"), \
         patch("pulsemon.cli_benchmark.get_monitor", return_value=_monitor), \
         patch("pulsemon.cli_benchmark.run_benchmark", return_value=_bench_result):
        handle_benchmark(_make_args(fmt="text"))
    out = capsys.readouterr().out
    assert "Avg" in out
    assert "P95" in out


def test_handle_benchmark_json_output(capsys, _monitor, _bench_result):
    with patch("pulsemon.cli_benchmark.get_connection"), \
         patch("pulsemon.cli_benchmark.get_monitor", return_value=_monitor), \
         patch("pulsemon.cli_benchmark.run_benchmark", return_value=_bench_result):
        handle_benchmark(_make_args(fmt="json"))
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["monitor_id"] == 1
    assert "avg_ms" in data
