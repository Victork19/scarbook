from app.contradiction import detect_contradiction


def envelope(verdict="bullish", risk="low", mode="live", status="ok"):
    return {"status": status, "data_mode": mode, "data": {"verdict": verdict, "risk": risk}}


def test_bullish_to_bearish_blocks_long():
    candidate = detect_contradiction(envelope(), envelope("bearish", "high"), {"side": "long"})
    assert candidate is not None
    assert candidate.constraint == "side_blocked"
    assert candidate.blocked_side == "long"


def test_risk_escalation_caps_size():
    candidate = detect_contradiction(envelope(), envelope("bullish", "medium"), {"side": "long"})
    assert candidate is not None
    assert candidate.constraint == "size_cap"
    assert candidate.max_size == 0.25


def test_unavailable_evidence_blocks_new_position():
    candidate = detect_contradiction(envelope(), envelope(mode="unavailable", status="error"), {"side": "long"})
    assert candidate is not None
    assert candidate.constraint == "no_new_position"
