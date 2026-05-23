"""Integration tests for cli_config using a real temporary TOML file."""

from __future__ import annotations

import io
import json
from pathlib import Path

import pytest

from pulsemon.cli_config import handle_config

import argparse


def _make_args(**kwargs) -> argparse.Namespace:
    defaults = {"config": None, "format": "text", "validate": False}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


@pytest.fixture()
def minimal_toml(tmp_path: Path) -> Path:
    p = tmp_path / "pulsemon.toml"
    p.write_text(
        '[pulsemon]\ndb_path = "test.db"\ncheck_interval = 30\nlog_level = "DEBUG"\n'
    )
    return p


@pytest.fixture()
def full_toml(tmp_path: Path) -> Path:
    p = tmp_path / "pulsemon.toml"
    p.write_text(
        "[pulsemon]\n"
        'db_path = "prod.db"\n'
        "check_interval = 120\n"
        'log_level = "WARNING"\n'
        "[alert]\n"
        'webhook_url = "https://hooks.example.com/abc"\n'
        'email_to = "ops@example.com"\n'
    )
    return p


def test_integration_text_output_minimal(minimal_toml: Path):
    out = io.StringIO()
    rc = handle_config(_make_args(config=str(minimal_toml)), out=out)
    assert rc == 0
    text = out.getvalue()
    assert "test.db" in text
    assert "30" in text


def test_integration_json_output_full(full_toml: Path):
    out = io.StringIO()
    rc = handle_config(_make_args(config=str(full_toml), format="json"), out=out)
    assert rc == 0
    data = json.loads(out.getvalue())
    assert data["db_path"] == "prod.db"
    assert data["check_interval"] == 120
    assert data["alert"]["webhook_url"] == "https://hooks.example.com/abc"


def test_integration_validate_passes(minimal_toml: Path):
    out = io.StringIO()
    rc = handle_config(_make_args(config=str(minimal_toml), validate=True), out=out)
    assert rc == 0


def test_integration_missing_file_returns_1(tmp_path: Path):
    missing = str(tmp_path / "nope.toml")
    rc = handle_config(_make_args(config=missing))
    assert rc == 1
