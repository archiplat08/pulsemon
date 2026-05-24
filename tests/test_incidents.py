"""Tests for pulsemon.incidents and pulsemon.cli_incidents."""
from __future__ import annotations

import io
import json
import sqlite3
import pytest

from pulsemon.incidents import (
    open_incident,
    resolve_incident,
    list_incidents,
    incident_as_dict,
    Incident,
)
from pulsemon.cli_incidents import add_incidents_parser, handle_incidents
from pulsemon.db import init_db


@pytest.fixture()
def conn(tmp_path):
    db = tmp_path / "test.db"
    c = sqlite3.connect(str(db))
    init_db(c)
    yield c
    c.close()


# --- unit tests for incidents module ---

def test_open_incident_returns_incident(conn):
    inc = open_incident(conn, monitor_id=1, started_at="2024-01-01T00:00:00")
    assert isinstance(inc, Incident)
    assert inc.id is not None
    assert inc.monitor_id == 1
    assert inc.resolved_at is None


def test_list_incidents_empty(conn):
    assert list_incidents(conn) == []


def test_list_incidents_returns_all(conn):
    open_incident(conn, monitor_id=1, started_at="2024-01-01T00:00:00")
    open_incident(conn, monitor_id=2, started_at="2024-01-02T00:00:00")
    incidents = list_incidents(conn)
    assert len(incidents) == 2


def test_list_incidents_filter_by_monitor(conn):
    open_incident(conn, monitor_id=1, started_at="2024-01-01T00:00:00")
    open_incident(conn, monitor_id=2, started_at="2024-01-02T00:00:00")
    result = list_incidents(conn, monitor_id=1)
    assert len(result) == 1
    assert result[0].monitor_id == 1


def test_list_incidents_open_only(conn):
    inc = open_incident(conn, monitor_id=1, started_at="2024-01-01T00:00:00")
    open_incident(conn, monitor_id=1, started_at="2024-01-03T00:00:00")
    resolve_incident(conn, inc.id, resolved_at="2024-01-02T00:00:00")
    open_only = list_incidents(conn, open_only=True)
    assert len(open_only) == 1
    assert open_only[0].resolved_at is None


def test_resolve_incident_sets_timestamp(conn):
    inc = open_incident(conn, monitor_id=1, started_at="2024-01-01T00:00:00")
    resolve_incident(conn, inc.id, resolved_at="2024-01-02T12:00:00")
    result = list_incidents(conn)
    assert result[0].resolved_at == "2024-01-02T12:00:00"


def test_incident_as_dict_shape(conn):
    inc = open_incident(conn, monitor_id=3, started_at="2024-05-01T08:00:00")
    d = incident_as_dict(inc)
    assert set(d.keys()) == {"id", "monitor_id", "started_at", "resolved_at"}
    assert d["monitor_id"] == 3


# --- CLI tests ---

@pytest.fixture()
def tmp_db_path(tmp_path):
    db = tmp_path / "pulsemon.db"
    c = sqlite3.connect(str(db))
    init_db(c)
    c.close()
    return str(db)


def _make_args(**kwargs):
    import argparse
    defaults = {"incidents_cmd": None, "db": None, "monitor_id": None, "open_only": False, "format": "text"}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_add_incidents_parser_registers_command():
    import argparse
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd")
    add_incidents_parser(sub)
    args = p.parse_args(["incidents", "list"])
    assert args.cmd == "incidents"


def test_handle_incidents_list_empty(tmp_db_path):
    args = _make_args(incidents_cmd="list", db=tmp_db_path)
    out = io.StringIO()
    handle_incidents(args, out=out)
    assert "No incidents" in out.getvalue()


def test_handle_incidents_list_json(tmp_db_path):
    c = sqlite3.connect(tmp_db_path)
    open_incident(c, monitor_id=1, started_at="2024-01-01T00:00:00")
    c.close()
    args = _make_args(incidents_cmd="list", db=tmp_db_path, format="json")
    out = io.StringIO()
    handle_incidents(args, out=out)
    data = json.loads(out.getvalue())
    assert isinstance(data, list)
    assert data[0]["monitor_id"] == 1


def test_handle_incidents_resolve(tmp_db_path):
    c = sqlite3.connect(tmp_db_path)
    inc = open_incident(c, monitor_id=1, started_at="2024-01-01T00:00:00")
    c.close()
    args = _make_args(incidents_cmd="resolve", db=tmp_db_path, incident_id=inc.id)
    out = io.StringIO()
    handle_incidents(args, out=out)
    assert "resolved" in out.getvalue().lower()
