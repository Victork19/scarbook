from __future__ import annotations

from dataclasses import dataclass
from typing import Any


RISK_ORDER = {"low": 1, "medium": 2, "high": 3}
BULLISH = {"bullish", "strong_bullish", "buy", "positive", "accumulate"}
BEARISH = {"bearish", "strong_bearish", "sell", "negative", "reduce", "avoid", "distribute"}


@dataclass(frozen=True)
class ConstraintCandidate:
    class_name: str
    constraint: str
    blocked_side: str | None
    max_size: float | None
    parameter: str | None
    reason: str


def trustworthy(evidence: dict[str, Any]) -> bool:
    return evidence.get("status") == "ok" and evidence.get("data_mode") in {"live", "fixture"}


def detect_contradiction(t0: dict[str, Any], t1: dict[str, Any], decision: dict[str, Any]) -> ConstraintCandidate | None:
    """Deterministically compile the highest-priority material contradiction."""
    if not trustworthy(t1):
        return ConstraintCandidate(
            "data",
            "no_new_position",
            None,
            None,
            "unavailable",
            "T1 evidence was not trustworthy because status is not ok or data_mode is not live/fixture.",
        )
    t0_data = t0.get("data") or {}
    t1_data = t1.get("data") or {}
    side = decision.get("side")
    if side == "long" and t0_data.get("verdict") in BULLISH and t1_data.get("verdict") in BEARISH:
        return ConstraintCandidate(
            "thesis",
            "side_blocked",
            "long",
            None,
            f"{t0_data.get('verdict')}->{t1_data.get('verdict')}",
            "The new live evidence contradicts the committed bullish thesis.",
        )
    if side == "short" and t0_data.get("verdict") in BEARISH and t1_data.get("verdict") in BULLISH:
        return ConstraintCandidate(
            "thesis",
            "side_blocked",
            "short",
            None,
            f"{t0_data.get('verdict')}->{t1_data.get('verdict')}",
            "The new live evidence contradicts the committed bearish thesis.",
        )
    t0_risk = t0_data.get("risk")
    t1_risk = t1_data.get("risk")
    if t0_risk in RISK_ORDER and t1_risk in RISK_ORDER and RISK_ORDER[t1_risk] > RISK_ORDER[t0_risk]:
        return ConstraintCandidate(
            "risk",
            "size_cap",
            None,
            0.25,
            f"{t0_risk}->{t1_risk}",
            "RYO risk escalated after the committed decision.",
        )
    return None
