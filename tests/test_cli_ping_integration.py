"""Integration tests for the ping subcommand (real HTTP mocked at socket level)."""
from __future__ import annotations

import argparse
import io
import sqlite3

import pytest
import responses

from pulsemon.cli_ping import handle_ping
from pulsemon.checks import get_latest_check
from pulsemon.db import get_connection, init_db
from pulsemon.monitors import create_monitor
from pulsemon.models import Monitor


@pytest.fixture()
def tmp_db_path(tmp_path):
    db_file = tmp_path / "ping_integ.db"
    conn = sqlite3.connect(str(db_file))
    init_db(conn)
    conn.close()
    return str(db_file)


def _make_args(**kwargs):
    defaults = {
        "monitor_id": 1,
        "db": "",
        "save": False,
        "format": "text",
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


@responses.activate
def test_ping_up_persists_when_save_true(tmp_db_path):
    responses.add(responses.GET, "https://example.com", status=200)

    conn = get_connection(tmp_db_path)
    m = Monitor(
        id=None,
        name="example",
        url="https://example.com",
        interval=60,
        timeout=5,
        created_at=None,
    )
    created = create_monitor(conn, m)
    conn.close()

    args = _make_args(monitor_id=created.id, db=tmp_db_path, save=True)
    rc = handle_ping(args, out=io.StringIO())
    assert rc == 0

    conn2 = get_connection(tmp_db_path)
    latest = get_latest_check(conn2, created.id)
    conn2.close()
    assert latest is not None
    assert latest.status == "up"


@responses.activate
def test_ping_down_does_not_persist_when_save_false(tmp_db_path):
    responses.add(responses.GET, "https://down.example.com", status=503)

    conn = get_connection(tmp_db_path)
    m = Monitor(
        id=None,
        name="down-example",
        url="https://down.example.com",
        interval=60,
        timeout=5,
        created_at=None,
    )
    created = create_monitor(conn, m)
    conn.close()

    args = _make_args(monitor_id=created.id, db=tmp_db_path, save=False)
    rc = handle_ping(args, out=io.StringIO())
    assert rc == 1

    conn2 = get_connection(tmp_db_path)
    latest = get_latest_check(conn2, created.id)
    conn2.close()
    assert latest is None
