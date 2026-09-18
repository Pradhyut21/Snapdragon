"""Small shared utilities."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4


def new_id(prefix: str) -> str:
    return f"{prefix}-{uuid4()}"


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
