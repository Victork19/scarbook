from app.normalize import normalize_response


def test_normalize_preserves_missing_values_and_source_mode():
    evidence = normalize_response(
        {"status": "ok", "data": {"verdict": "BULLISH", "risk": "LOW"}},
        symbol="SOL",
        tool="analyze_token",
        data_mode="live",
    )
    assert evidence.data.verdict == "bullish"
    assert evidence.data.risk == "low"
    assert evidence.data.rsi14 is None
    assert evidence.data_mode == "live"
