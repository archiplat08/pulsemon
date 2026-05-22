"""Data models for pulsemon."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Monitor:
    """Represents a monitored endpoint."""
    url: str
    name: str
    interval_seconds: int = 60
    timeout_seconds: int = 10
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    is_active: bool = True

    def __post_init__(self):
        if self.interval_seconds < 10:
            raise ValueError("interval_seconds must be at least 10")
        if self.timeout_seconds < 1:
            raise ValueError("timeout_seconds must be at least 1")
        if not self.url.startswith(("http://", "https://")):
            raise ValueError("url must start with http:// or https://")
        if not self.name.strip():
            raise ValueError("name must not be empty")


@dataclass
class CheckResult:
    """Represents the result of a single uptime check."""
    monitor_id: int
    status_code: Optional[int]
    response_time_ms: Optional[float]
    is_up: bool
    checked_at: datetime = field(default_factory=datetime.utcnow)
    error_message: Optional[str] = None
    id: Optional[int] = None
