from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .schemas import EvidenceData, NormalizedEvidence


def _first(mapping: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in mapping:
            return mapping[key]
    return None


def normalize_response(
    raw: dict[str, Any],
    *,
    symbol: str,
    tool: str,
    data_mode: str,
    default_status: str = "ok",
) -> NormalizedEvidence:
    """Adapt RYO/fixture variants into the one envelope used by the runtime."""
    raw = raw or {}
    nested = raw.get("data") if isinstance(raw.get("data"), dict) else {}
    source = {**raw, **nested}
    technical = nested.get("technical_analysis") if isinstance(nested.get("technical_analysis"), dict) else {}
    status = str(_first(raw, "status") or _first(nested, "status") or default_status)
    mode = str(_first(raw, "data_mode", "mode") or _first(nested, "data_mode", "mode") or data_mode)
    if mode not in {"live", "fixture", "unavailable", "error"}:
        mode = "error"
    timestamp = _first(raw, "as_of", "timestamp", "observed_at") or _first(
        nested, "as_of", "timestamp", "observed_at"
    )
    try:
        as_of = datetime.now(timezone.utc) if not timestamp else datetime.fromisoformat(str(timestamp).replace("Z", "+00:00"))
    except ValueError:
        as_of = datetime.now(timezone.utc)
    verdict = _first(source, "verdict", "signal", "market_verdict")
    risk = _first(source, "risk", "risk_level")
    rsi = _first(source, "rsi14", "rsi_14", "rsi")
    if rsi is None:
        rsi = _first(technical, "rsi14", "rsi_14", "rsi")
    try:
        rsi = None if rsi is None else float(rsi)
    except (TypeError, ValueError):
        rsi = None
    warnings = _first(raw, "warnings") or _first(nested, "warnings") or []
    if isinstance(warnings, str):
        warnings = [warnings]
    return NormalizedEvidence(
        schema_version="1.0",
        tool=tool,
        status=status,
        data_mode=mode,
        as_of=as_of,
        request={"symbol": symbol},
        data=EvidenceData(verdict=None if verdict is None else str(verdict).lower(), risk=None if risk is None else str(risk).lower(), rsi14=rsi),
        warnings=list(warnings),
    )
