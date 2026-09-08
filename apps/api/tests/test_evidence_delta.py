from app.evidence_delta import compare_evidence


def evidence(verdict, risk, rsi14, *, mode="fixture", status="ok"):
    return {
        "status": status,
        "data_mode": mode,
        "as_of": "2026-09-08T10:00:00Z",
        "data": {"verdict": verdict, "risk": risk, "rsi14": rsi14},
        "warnings": [],
    }


def test_evidence_delta_reports_material_change():
    result = compare_evidence(
        "SOL",
        evidence("bullish", "low", 64.2),
        evidence("bearish", "high", 38.7),
    )
    assert result["status"] == "ok"
    assert result["data"]["state"] == "changed"
    assert result["data"]["transition"] == "bullish->bearish"
    assert {item["field"] for item in result["data"]["changes"]} == {"verdict", "risk", "rsi14"}
    assert len(result["observations"][0]["evidence_hash"]) == 64
    assert len(result["observations"][1]["hash_short"]) == 8


def test_evidence_delta_reports_unchanged_without_inference():
    result = compare_evidence("SOL", evidence("accumulate", None, 63.3), evidence("accumulate", None, 63.3))
    assert result["status"] == "partial"
    assert result["data"]["state"] == "insufficient_evidence"
    assert result["data"]["changes"] == []
    assert "risk" in result["data"]["missing_fields"]


def test_evidence_delta_is_honest_when_source_is_unavailable():
    result = compare_evidence(
        "SOL",
        evidence(None, None, None, mode="unavailable", status="error"),
        evidence("bullish", "low", 64.2),
    )
    assert result["status"] == "partial"
    assert result["data"]["state"] == "insufficient_evidence"
    assert result["data"]["changes"] == []
    assert result["warnings"]


def test_evidence_delta_does_not_compare_mixed_modes():
    result = compare_evidence(
        "SOL",
        evidence("bullish", "low", 64.2, mode="live"),
        evidence("bearish", "high", 38.7, mode="fixture"),
    )
    assert result["status"] == "partial"
    assert result["data"]["state"] == "insufficient_evidence"
    assert result["data"]["transition"] is None
    assert result["data"]["changes"] == []
