from __future__ import annotations

from .contradiction import ConstraintCandidate


def compile_constraint(candidate: ConstraintCandidate, *, constraint_id: str, symbol: str, decision: dict, t0: dict, t1: dict) -> dict:
    t0_time = str(t0.get("as_of", "")).replace("T", " ").replace("Z", " UTC")[:19]
    t1_time = str(t1.get("as_of", "")).replace("T", " ").replace("Z", " UTC")[:19]
    t0_data = t0.get("data") or {}
    t1_data = t1.get("data") or {}
    if candidate.constraint == "side_blocked":
        citation = (
            f"RYO verdict changed from {t0_data.get('verdict')} at T0 to {t1_data.get('verdict')} at T1 "
            f"between {t0_time} and {t1_time}. Constraint {constraint_id}: {candidate.blocked_side.upper()} blocked."
        )
        policy = {"long": "ALLOW", "short": "ALLOW", "none": "ALLOW"}
        policy[candidate.blocked_side or "long"] = "DENY"
    elif candidate.constraint == "size_cap":
        citation = (
            f"RYO risk increased from {t0_data.get('risk')} at T0 to {t1_data.get('risk')} at T1. "
            f"Constraint {constraint_id}: maximum practice size = {candidate.max_size}."
        )
        policy = {"long": {"max_size": candidate.max_size}, "short": {"max_size": candidate.max_size}}
    else:
        citation = f"T1 evidence was not trustworthy. Constraint {constraint_id}: no new position."
        policy = {"long": "DENY", "short": "DENY", "none": "ALLOW"}
    return {
        "id": constraint_id,
        "symbol": symbol,
        "source_decision_id": decision["id"],
        "trigger_receipt_id": t1["id"],
        "class": candidate.class_name,
        "constraint": candidate.constraint,
        "parameter": candidate.parameter,
        "blocked_side": candidate.blocked_side,
        "max_size": candidate.max_size,
        "reason": candidate.reason,
        "citation": citation,
        "action_policy": policy,
    }

