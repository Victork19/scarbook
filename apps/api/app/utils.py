from __future__ import annotations

from datetime import datetime, timezone
import re


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def public_id(prefix: str, number: int) -> str:
    return f"{prefix}-{number:03d}"


def short_hash(value: str) -> str:
    return value[:8].upper()


def safe_symbol(value: str) -> str:
    return re.sub(r"[^A-Z0-9._-]", "", value.upper())[:20]

