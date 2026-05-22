"""Configuration loader for pulsemon.

Reads a TOML config file (pulsemon.toml by default) and exposes a
typed Config dataclass.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

try:
    import tomllib  # Python 3.11+
except ImportError:  # pragma: no cover
    import tomli as tomllib  # type: ignore[no-reattr]


DEFAULT_CONFIG_PATH = "pulsemon.toml"


@dataclass
class SmtpConfig:
    host: str
    port: int = 587
    username: str = ""
    password: str = ""
    from_addr: str = ""
    to_addrs: list[str] = field(default_factory=list)
    use_tls: bool = True


@dataclass
class AlertConfig:
    webhook_url: str = ""
    smtp: SmtpConfig | None = None

    def as_dict(self) -> dict:
        d: dict = {}
        if self.webhook_url:
            d["webhook_url"] = self.webhook_url
        if self.smtp:
            d["smtp"] = vars(self.smtp)
        return d


@dataclass
class Config:
    db_path: str = "pulsemon.db"
    tick_seconds: int = 30
    alerts: AlertConfig = field(default_factory=AlertConfig)


def load_config(path: str | Path | None = None) -> Config:
    """Load configuration from a TOML file.

    Falls back to environment variable PULSEMON_CONFIG, then DEFAULT_CONFIG_PATH.
    Returns default Config if the file does not exist.
    """
    if path is None:
        path = os.environ.get("PULSEMON_CONFIG", DEFAULT_CONFIG_PATH)

    config_path = Path(path)
    if not config_path.exists():
        return Config()

    with config_path.open("rb") as fh:
        raw = tomllib.load(fh)

    db_path = raw.get("db_path", "pulsemon.db")
    tick_seconds = int(raw.get("tick_seconds", 30))

    alert_section = raw.get("alerts", {})
    webhook_url = alert_section.get("webhook_url", "")

    smtp_cfg: SmtpConfig | None = None
    if smtp_raw := alert_section.get("smtp"):
        smtp_cfg = SmtpConfig(
            host=smtp_raw["host"],
            port=int(smtp_raw.get("port", 587)),
            username=smtp_raw.get("username", ""),
            password=smtp_raw.get("password", ""),
            from_addr=smtp_raw.get("from_addr", ""),
            to_addrs=smtp_raw.get("to_addrs", []),
            use_tls=bool(smtp_raw.get("use_tls", True)),
        )

    return Config(
        db_path=db_path,
        tick_seconds=tick_seconds,
        alerts=AlertConfig(webhook_url=webhook_url, smtp=smtp_cfg),
    )
