"""Unit tests for pulsemon.search."""
from __future__ import annotations

import pytest

from pulsemon.db import init_db
from pulsemon.monitors import create_monitor
from pulsemon.models import Monitor
from pulsemon.search import search_monitors, search_result_as_dict


@pytest.fixture()
def tmp_db(tmp_path):
    import sqlite3
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    init_db(conn)
    return conn


def _make_monitor(name="Alpha", url="https://alpha.example.com", tags="web"):
    return Monitor(name=name, url=url, interval=60, timeout=10, tags=tags)


def test_search_by_name_finds_match(tmp_db):
    create_monitor(tmp_db, _make_monitor(name="AlphaService"))
    create_monitor(tmp_db, _make_monitor(name="BetaService", url="https://beta.example.com"))
    results = search_monitors(tmp_db, "Alpha", field="name")
    assert len(results) == 1
    assert results[0].name == "AlphaService"


def test_search_by_url_finds_match(tmp_db):
    create_monitor(tmp_db, _make_monitor(url="https://api.example.com"))
    create_monitor(tmp_db, _make_monitor(name="Other", url="https://other.io"))
    results = search_monitors(tmp_db, "api.example", field="url")
    assert len(results) == 1
    assert "api.example" in results[0].url


def test_search_by_tag_finds_match(tmp_db):
    create_monitor(tmp_db, _make_monitor(tags="web,critical"))
    create_monitor(tmp_db, _make_monitor(name="B", url="https://b.example.com", tags="internal"))
    results = search_monitors(tmp_db, "critical", field="tag")
    assert len(results) == 1
    assert "critical" in results[0].tags


def test_search_any_matches_across_fields(tmp_db):
    create_monitor(tmp_db, _make_monitor(name="gamma", url="https://gamma.io", tags="ops"))
    create_monitor(tmp_db, _make_monitor(name="delta", url="https://delta.io", tags="ops"))
    results = search_monitors(tmp_db, "gamma", field="any")
    assert len(results) == 1
    assert results[0].name == "gamma"


def test_search_returns_empty_when_no_match(tmp_db):
    create_monitor(tmp_db, _make_monitor())
    results = search_monitors(tmp_db, "zzznomatch", field="any")
    assert results == []


def test_search_case_insensitive(tmp_db):
    create_monitor(tmp_db, _make_monitor(name="MyService"))
    results = search_monitors(tmp_db, "myservice", field="name")
    assert len(results) == 1


def test_search_result_as_dict_has_required_keys(tmp_db):
    m = create_monitor(tmp_db, _make_monitor())
    d = search_result_as_dict(m)
    for key in ("id", "name", "url", "interval", "timeout", "tags", "created_at"):
        assert key in d
