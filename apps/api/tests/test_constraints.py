from app.db import Database


def test_wipe_deactivates_but_preserves_history(tmp_path):
    database = Database(path=str(tmp_path / "scarbook.db"))
    session = database.create_session("SOL")
    evidence = {
        "tool": "analyze_token", "as_of": "2026-09-08T10:00:00Z", "status": "ok", "data_mode": "live",
        "data": {"verdict": "bullish", "risk": "low"}, "request": {"symbol": "SOL"},
    }
    receipt = database.create_receipt(session_id=session["id"], symbol="SOL", phase="t0", evidence=evidence, evidence_hash="a" * 64)
    decision = database.create_decision(session_id=session["id"], receipt_id=receipt["id"], decision={"symbol": "SOL", "side": "long", "size": 1, "thesis": "x", "confidence": 0.5, "evidence_used": []})
    database.create_constraint({
        "symbol": "SOL", "source_decision_id": decision["id"], "trigger_receipt_id": receipt["id"], "class": "thesis",
        "constraint": "side_blocked", "blocked_side": "long", "max_size": None, "parameter": "x", "reason": "x",
        "citation": "x", "action_policy": {"long": "DENY"},
    })
    assert len(database.constraints("SOL", active_only=True)) == 1
    assert database.deactivate_constraints("SOL") == 1
    assert len(database.constraints("SOL", active_only=True)) == 0
    assert len(database.constraints("SOL", active_only=False)) == 1
