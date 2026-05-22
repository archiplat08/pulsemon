"""Tests for pulsemon.monitors CRUD operations."""
import pytest
from pathlib import Path

from pulsemon.db import init_db, db_conn
from pulsemon.models import Monitor
from pulsemon import monitors as mon_crud


@pytest.fixture()
def tmp_db(tmp_path: Path, monkeypatch):
    db_file = tmp_path / "test.db"
    init_db(db_file)
    monkeypatch.setattr("pulsemon.db.DB_PATH", db_file)
    monkeypatch.setattr("pulsemon.monitors.db_conn",
                        lambda: db_conn(db_file))
    return db_file


def _make_monitor(**kwargs) -> Monitor:
    defaults = dict(url="https://example.com", name="Example", interval_seconds=30)
    defaults.update(kwargs)
    return Monitor(**defaults)


def test_create_monitor_assigns_id(tmp_db):
    m = mon_crud.create_monitor(_make_monitor())
    assert m.id is not None
    assert m.id > 0


def test_create_monitor_sets_created_at(tmp_db):
    m = mon_crud.create_monitor(_make_monitor())
    assert m.created_at is not None


def test_get_monitor_returns_correct_row(tmp_db):
    created = mon_crud.create_monitor(_make_monitor(name="My Site"))
    fetched = mon_crud.get_monitor(created.id)
    assert fetched is not None
    assert fetched.name == "My Site"
    assert fetched.url == "https://example.com"


def test_get_monitor_returns_none_for_missing(tmp_db):
    assert mon_crud.get_monitor(9999) is None


def test_list_monitors_returns_all(tmp_db):
    mon_crud.create_monitor(_make_monitor(name="A"))
    mon_crud.create_monitor(_make_monitor(name="B", url="https://b.example.com"))
    results = mon_crud.list_monitors()
    assert len(results) == 2


def test_list_monitors_active_only(tmp_db):
    mon_crud.create_monitor(_make_monitor(name="Active"))
    inactive = _make_monitor(name="Inactive", url="https://inactive.example.com")
    inactive.is_active = False
    mon_crud.create_monitor(inactive)
    results = mon_crud.list_monitors(active_only=True)
    assert all(r.is_active for r in results)
    assert len(results) == 1


def test_delete_monitor_removes_row(tmp_db):
    m = mon_crud.create_monitor(_make_monitor())
    deleted = mon_crud.delete_monitor(m.id)
    assert deleted is True
    assert mon_crud.get_monitor(m.id) is None


def test_delete_monitor_returns_false_for_missing(tmp_db):
    assert mon_crud.delete_monitor(9999) is False
