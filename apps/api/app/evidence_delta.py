from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


TRUSTED_MODES = {"live", "fixture"}
FIELDS = ("verdict", "risk", "rsi14")


def _data(evidence: dict[str, Any]) -> dict[str, Any]:
    value = evidence.get("data")
    return value if isinstance(value, dict) else {}


def _as_of(evidence: dict[str, Any]) -> str:
    value = evidence.get("as_of")
    if value:
        return str(value)
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _trustworthy(evidence: dict[str, Any]) -> bool:
    return evidence.get("status") == "ok" and evidence.get("data_mode") in TRUSTED_MODES


def _observation(label: str, evidence: dict[str, Any]) -> dict[str, Any]:
    data = _data(evidence)
    return {
        "label": label,
        "as_of": _as_of(evidence),
        "status": evidence.get("status"),
        "data_mode": evidence.get("data_mode"),
        "data": {field: data.get(field) for field in FIELDS},
        "warnings": list(evidence.get("warnings") or []),
    }


def compare_evidence(symbol: str, before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    """Build a deterministic, honest delta between two normalized observations."""
    before_data = _data(before)
    after_data = _data(after)
    warnings = [*(before.get("warnings") or []), *(after.get("warnings") or [])]
    missing_fields: list[str] = []
    changes: list[dict[str, Any]] = []

    for field in FIELDS:
        old = before_data.get(field)
        new = after_data.get(field)
        if old is None or new is None:
            missing_fields.append(field)
            continue
        if old == new:
            continue
        change: dict[str, Any] = {"field": field, "before": old, "after": new}
        if isinstance(old, (int, float)) and isinstance(new, (int, float)):
            change["delta"] = round(float(new) - float(old), 6)
        changes.append(change)

    trustworthy = _trustworthy(before) and _trustworthy(after)
    same_mode = before.get("data_mode") == after.get("data_mode")
    comparable = trustworthy and same_mode
    if not comparable:
        status = "unavailable" if not _trustworthy(before) and not _trustworthy(after) else "partial"
        state = "insufficient_evidence"
        if trustworthy and not same_mode:
            warnings.append("Observations use different data modes and were not compared as a complete delta.")
        else:
            warnings.append("A complete delta requires two successful live or fixture observations.")
    else:
        status = "ok"
        state = "changed" if changes else "unchanged"

    before_verdict = before_data.get("verdict")
    after_verdict = after_data.get("verdict")
    transition = None
    if comparable and before_verdict is not None and after_verdict is not None and before_verdict != after_verdict:
        transition = f"{before_verdict}->{after_verdict}"

    if not comparable:
        changes = []

    data_modes = {before.get("data_mode"), after.get("data_mode")}
    if not trustworthy:
        data_mode = "unavailable"
    elif len(data_modes) == 1:
        data_mode = next(iter(data_modes))
    else:
        data_mode = "mixed"

    return {
        "schema_version": "1.0",
        "tool": "evidence_delta",
        "status": status,
        "data_mode": data_mode,
        "as_of": _as_of(after),
        "request": {"symbol": symbol},
        "data": {
            "state": state,
            "transition": transition,
            "changes": changes,
            "missing_fields": sorted(set(missing_fields)),
            "before": {field: before_data.get(field) for field in FIELDS},
            "after": {field: after_data.get(field) for field in FIELDS},
        },
        "observations": [_observation("before", before), _observation("after", after)],
        "warnings": sorted(set(warnings)),
    }


EVIDENCE_DELTA_TOOL = {
    "name": "evidence_delta",
    "description": (
        "Compare two sequential RYO analyze_token observations for one symbol. "
        "Returns explicit changes, unchanged state, or an honest unavailable/partial result; "
        "never infers missing market data. Read-only."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {
            "symbol": {
                "type": "string",
                "minLength": 1,
                "maxLength": 20,
                "description": "Token symbol, for example SOL.",
            }
        },
        "required": ["symbol"],
        "additionalProperties": False,
    },
}
