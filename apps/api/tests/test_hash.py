from app.hashing import evidence_hash


def test_hash_is_stable_and_ignores_display_fields():
    evidence = {
        "schema_version": "1.0",
        "tool": "analyze_token",
        "status": "ok",
        "data_mode": "live",
        "as_of": "2026-09-08T10:00:00Z",
        "request": {"symbol": "SOL"},
        "data": {"verdict": "bullish", "risk": "low", "rsi14": 64.2},
        "warnings": [],
    }
    changed = {**evidence, "summary": "display-only"}
    assert evidence_hash(evidence) == evidence_hash(changed)
