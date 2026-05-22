"""Tests for pulsemon.config."""

import pytest
from pathlib import Path

from pulsemon.config import load_config, Config, AlertConfig, SmtpConfig


MINIMAL_TOML = """
db_path = "data/pulsemon.db"
tick_seconds = 60
"""

FULL_TOML = """
db_path = "prod.db"
tick_seconds = 15

[alerts]
webhook_url = "https://hooks.example.com/xyz"

[alerts.smtp]
host = "smtp.example.com"
port = 465
username = "user@example.com"
password = "s3cret"
from_addr = "alerts@example.com"
to_addrs = ["ops@example.com", "dev@example.com"]
use_tls = true
"""


def test_load_config_missing_file_returns_defaults(tmp_path):
    cfg = load_config(str(tmp_path / "nonexistent.toml"))
    assert isinstance(cfg, Config)
    assert cfg.db_path == "pulsemon.db"
    assert cfg.tick_seconds == 30


def test_load_config_minimal(tmp_path):
    p = tmp_path / "pulsemon.toml"
    p.write_text(MINIMAL_TOML)
    cfg = load_config(p)
    assert cfg.db_path == "data/pulsemon.db"
    assert cfg.tick_seconds == 60
    assert cfg.alerts.webhook_url == ""
    assert cfg.alerts.smtp is None


def test_load_config_full(tmp_path):
    p = tmp_path / "pulsemon.toml"
    p.write_text(FULL_TOML)
    cfg = load_config(p)
    assert cfg.db_path == "prod.db"
    assert cfg.tick_seconds == 15
    assert cfg.alerts.webhook_url == "https://hooks.example.com/xyz"
    smtp = cfg.alerts.smtp
    assert isinstance(smtp, SmtpConfig)
    assert smtp.host == "smtp.example.com"
    assert smtp.port == 465
    assert smtp.to_addrs == ["ops@example.com", "dev@example.com"]
    assert smtp.use_tls is True


def test_load_config_env_var(tmp_path, monkeypatch):
    p = tmp_path / "custom.toml"
    p.write_text(MINIMAL_TOML)
    monkeypatch.setenv("PULSEMON_CONFIG", str(p))
    cfg = load_config()
    assert cfg.tick_seconds == 60


def test_alert_config_as_dict_empty():
    ac = AlertConfig()
    assert ac.as_dict() == {}


def test_alert_config_as_dict_with_webhook():
    ac = AlertConfig(webhook_url="https://example.com/hook")
    d = ac.as_dict()
    assert d["webhook_url"] == "https://example.com/hook"
    assert "smtp" not in d


def test_alert_config_as_dict_with_smtp():
    smtp = SmtpConfig(host="smtp.example.com", from_addr="a@b.com", to_addrs=["x@b.com"])
    ac = AlertConfig(smtp=smtp)
    d = ac.as_dict()
    assert d["smtp"]["host"] == "smtp.example.com"
