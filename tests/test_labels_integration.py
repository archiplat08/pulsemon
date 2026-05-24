"""Integration tests: labels survive a real SQLite round-trip."""
from __future__ import annotations

import sqlite3
import pytest

from pulsemon.labels import (
    clear_labels,
    get_labels,
    remove_label,
    set_label,
)


@pytest.fixture()
def conn(tmp_path):
    db_path = tmp_path / "int.db"
    c = sqlite3.connect(str(db_path))
    yield c
    c.close()


def test_labels_persist_across_calls(conn):
    set_label(conn, 10, "env", "prod")
    set_label(conn, 10, "owner", "alice")
    result = get_labels(conn, 10)
    assert result == {"env": "prod", "owner": "alice"}


def test_overwrite_then_read(conn):
    set_label(conn, 1, "stage", "alpha")
    set_label(conn, 1, "stage", "beta")
    assert get_labels(conn, 1)["stage"] == "beta"


def test_remove_then_set_same_key(conn):
    set_label(conn, 2, "k", "v1")
    remove_label(conn, 2, "k")
    set_label(conn, 2, "k", "v2")
    assert get_labels(conn, 2)["k"] == "v2"


def test_clear_then_repopulate(conn):
    for i in range(5):
        set_label(conn, 3, f"key{i}", str(i))
    clear_labels(conn, 3)
    assert get_labels(conn, 3) == {}
    set_label(conn, 3, "fresh", "yes")
    assert get_labels(conn, 3) == {"fresh": "yes"}


def test_multiple_monitors_independent(conn):
    set_label(conn, 100, "x", "a")
    set_label(conn, 200, "x", "b")
    clear_labels(conn, 100)
    assert get_labels(conn, 100) == {}
    assert get_labels(conn, 200) == {"x": "b"}
