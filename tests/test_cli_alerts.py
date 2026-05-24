"""Unit tests for pulsemon.cli_alerts."""
from __future__ import annotations

import argparse
import json
import sqlite3
from io import StringIO
from unittest.mock import patch

import pytest

from pulsemon.db import init_db
from pulsemon.alert_log import save_alert_log
from pulsemon.cli_alerts import add_alerts_parser, handle_alerts


@pytest.fixture()
def tmp_db_path(tmp_path):
    db = tmp_path / "test.db"
    conn = sqlite3.connect(str(db))
    init_db(conn)
    conn.close()
    return str(db)


def _make_args(**kwargs):
    defaults = {"db": ":memory:", "fmt": "text", "limit": 50, "alerts_cmd": "list"}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_add_alerts_parser_registers_command():
    root = argparse.ArgumentParser()
    sub = root.add_subparsers(dest="cmd")
    add_alerts_parser(sub)
    args = root.parse_args(["alerts"])
    assert args.cmd == "alerts"


def test_handle_alerts_list_empty(tmp_db_path, capsys):
    args = _make_args(db=tmp_db_path, alerts_cmd="list")
    handle_alerts(args)
    out = capsys.readouterr().out
    assert "No alerts" in out


def test_handle_alerts_list_text(tmp_db_path, capsys):
    conn = sqlite3.connect(tmp_db_path)
    init_db(conn)
    save_alert_log(conn, 1, "SiteA", "webhook", False)
    conn.close()
    args = _make_args(db=tmp_db_path, alerts_cmd="list")
    handle_alerts(args)
    out = capsys.readouterr().out
    assert "SiteA" in out
    assert "DOWN" in out


def test_handle_alerts_list_json(tmp_db_path, capsys):
    conn = sqlite3.connect(tmp_db_path)
    init_db(conn)
    save_alert_log(conn, 1, "SiteB", "email", True)
    conn.close()
    args = _make_args(db=tmp_db_path, alerts_cmd="list", fmt="json")
    handle_alerts(args)
    data = json.loads(capsys.readouterr().out)
    assert isinstance(data, list)
    assert data[0]["monitor_name"] == "SiteB"


def test_handle_alerts_clear_with_yes_flag(tmp_db_path, capsys):
    conn = sqlite3.connect(tmp_db_path)
    init_db(conn)
    save_alert_log(conn, 1, "SiteC", "webhook", False)
    conn.close()
    args = _make_args(db=tmp_db_path, alerts_cmd="clear", yes=True)
    handle_alerts(args)
    out = capsys.readouterr().out
    assert "Deleted 1" in out


def test_handle_alerts_clear_aborted(tmp_db_path, capsys):
    args = _make_args(db=tmp_db_path, alerts_cmd="clear", yes=False)
    with patch("builtins.input", return_value="n"):
        handle_alerts(args)
    out = capsys.readouterr().out
    assert "Aborted" in out
