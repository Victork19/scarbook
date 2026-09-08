from __future__ import annotations

import hashlib
import json
from typing import Any


def canonical_evidence(evidence: dict[str, Any]) -> dict[str, Any]:
    """Return only decision-relevant fields in a stable shape."""
    data = evidence.get("data") or {}
    request = evidence.get("request") or {}
    return {
        "symbol": request.get("symbol"),
        "tool": evidence.get("tool"),
        "schema_version": evidence.get("schema_version", "1.0"),
        "status": evidence.get("status"),
        "data_mode": evidence.get("data_mode"),
        "as_of": evidence.get("as_of"),
        "verdict": data.get("verdict"),
        "risk": data.get("risk"),
        "rsi14": data.get("rsi14"),
    }


def evidence_hash(evidence: dict[str, Any]) -> str:
    canonical = json.dumps(
        canonical_evidence(evidence),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

