"""Unit tests for pulsemon.labels."""
from __future__ import annotations

import sqlite3
import pytest

from pulsemon.labels import (
    get_labels,
    set_label,
    remove_label,
    clear_labels,
)


@pytest.fixture()
def conn():
    c = sqlite3.connect(":memory:")
    yield c
    c.close()


def test_get_labels_empty_db(conn):
    result = get_labels(conn, 1)
    assert result == {}


def test_set_label_and_retrieve(conn):
    set_label(conn, 1, "env", "prod")
    labels = get_labels(conn, 1)
    assert labels == {"env": "prod"}


def test_set_label_overwrites_existing(conn):
    set_label(conn, 1, "env", "staging")
    set_label(conn, 1, "env", "prod")
    labels = get_labels(conn, 1)
    assert labels["env"] == "prod"


def test_set_multiple_labels(conn):
    set_label(conn, 2, "env", "prod")
    set_label(conn, 2, "team", "backend")
    labels = get_labels(conn, 2)
    assert labels == {"env": "prod", "team": "backend"}


def test_remove_label_deletes_key(conn):
    set_label(conn, 1, "env", "prod")
    set_label(conn, 1, "region", "us-east")
    remove_label(conn, 1, "env")
    labels = get_labels(conn, 1)
    assert "env" not in labels
    assert labels["region"] == "us-east"


def test_remove_label_nonexistent_is_noop(conn):
    # Should not raise
    remove_label(conn, 99, "missing")


def test_clear_labels_removes_all(conn):
    set_label(conn, 3, "a", "1")
    set_label(conn, 3, "b", "2")
    clear_labels(conn, 3)
    assert get_labels(conn, 3) == {}


def test_labels_are_isolated_per_monitor(conn):
    set_label(conn, 1, "env", "prod")
    set_label(conn, 2, "env", "dev")
    assert get_labels(conn, 1) == {"env": "prod"}
    assert get_labels(conn, 2) == {"env": "dev"}


def test_get_labels_returns_sorted_keys(conn):
    set_label(conn, 5, "z", "last")
    set_label(conn, 5, "a", "first")
    set_label(conn, 5, "m", "mid")
    keys = list(get_labels(conn, 5).keys())
    assert keys == sorted(keys)
