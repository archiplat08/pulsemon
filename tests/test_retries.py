"""Tests for pulsemon.retries module."""
from __future__ import annotations

import sqlite3

import pytest

from pulsemon.retries import (
    RetryConfig,
    get_retry_config,
    set_retry_config,
    _DEFAULT_MAX_RETRIES,
    _DEFAULT_RETRY_DELAY,
)


@pytest.fixture
def conn():
    c = sqlite3.connect(":memory:")
    yield c
    c.close()


def test_get_retry_config_returns_defaults_when_not_set(conn):
    cfg = get_retry_config(conn, monitor_id=1)
    assert isinstance(cfg, RetryConfig)
    assert cfg.monitor_id == 1
    assert cfg.max_retries == _DEFAULT_MAX_RETRIES
    assert cfg.retry_delay == _DEFAULT_RETRY_DELAY


def test_set_retry_config_persists_values(conn):
    cfg = set_retry_config(conn, 42, max_retries=5, retry_delay=10.0)
    assert cfg.max_retries == 5
    assert cfg.retry_delay == 10.0

    fetched = get_retry_config(conn, 42)
    assert fetched.max_retries == 5
    assert fetched.retry_delay == 10.0


def test_set_retry_config_overwrites_existing(conn):
    set_retry_config(conn, 1, max_retries=2, retry_delay=3.0)
    set_retry_config(conn, 1, max_retries=7, retry_delay=1.5)
    cfg = get_retry_config(conn, 1)
    assert cfg.max_retries == 7
    assert cfg.retry_delay == 1.5


def test_set_retry_config_rejects_max_retries_zero(conn):
    with pytest.raises(ValueError, match="max_retries"):
        set_retry_config(conn, 1, max_retries=0)


def test_set_retry_config_rejects_max_retries_above_ten(conn):
    with pytest.raises(ValueError, match="max_retries"):
        set_retry_config(conn, 1, max_retries=11)


def test_set_retry_config_rejects_negative_delay(conn):
    with pytest.raises(ValueError, match="retry_delay"):
        set_retry_config(conn, 1, retry_delay=-1.0)


def test_set_retry_config_allows_zero_delay(conn):
    cfg = set_retry_config(conn, 1, max_retries=1, retry_delay=0.0)
    assert cfg.retry_delay == 0.0


def test_multiple_monitors_independent(conn):
    set_retry_config(conn, 1, max_retries=2, retry_delay=1.0)
    set_retry_config(conn, 2, max_retries=8, retry_delay=30.0)
    assert get_retry_config(conn, 1).max_retries == 2
    assert get_retry_config(conn, 2).max_retries == 8
