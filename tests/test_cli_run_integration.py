"""Integration test: handle_run --once against a real (temp) SQLite database."""
from __future__ import annotations

import argparse
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from pulsemon.cli_run import handle_run
from pulsemon.db import get_connection, init_db
from pulsemon.monitors import create_monitor
from pulsemon.models import Monitor


@pytest.fixture()
def tmp_db_path(tmp_path: Path) -> str:
    db = str(tmp_path / "test.db")
    init_db(db)
    return db


def _make_args(db: str, once: bool = True) -> argparse.Namespace:
    return argparse.Namespace(config="pulsemon.toml", db=db, once=once)


def test_handle_run_once_with_no_monitors_does_not_crash(tmp_db_path: str):
    """Scheduler.run_once() should complete cleanly when there are no monitors."""
    cfg = MagicMock()
    cfg.db_path = tmp_db_path
    cfg.alert = MagicMock()
    cfg.alert.webhook_url = None
    cfg.alert.smtp = None

    with patch("pulsemon.cli_run.load_config", return_value=cfg):
        handle_run(_make_args(db=tmp_db_path, once=True))

    # No exception means success; verify DB is still intact
    with get_connection(tmp_db_path) as conn:
        row = conn.execute("SELECT COUNT(*) FROM monitors").fetchone()
    assert row[0] == 0


def test_handle_run_once_persists_check_result(tmp_db_path: str):
    """After run_once a check result should be stored for each monitor."""
    m = Monitor(name="integration", url="http://example.com", interval=60, timeout=5)
    with get_connection(tmp_db_path) as conn:
        create_monitor(conn, m)

    cfg = MagicMock()
    cfg.db_path = tmp_db_path
    cfg.alert = MagicMock()
    cfg.alert.webhook_url = None
    cfg.alert.smtp = None

    fake_result = MagicMock()
    fake_result.status = "up"
    fake_result.monitor_id = 1

    with patch("pulsemon.cli_run.load_config", return_value=cfg), \
         patch("pulsemon.scheduler.check_monitor", return_value=fake_result), \
         patch("pulsemon.scheduler.save_check_result") as mock_save:
        handle_run(_make_args(db=tmp_db_path, once=True))

    mock_save.assert_called_once()
