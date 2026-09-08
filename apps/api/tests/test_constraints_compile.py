from app.constraints import compile_constraint
from app.contradiction import ConstraintCandidate


def test_compile_constraint_uses_t1_receipt_id():
    candidate = ConstraintCandidate(
        "thesis",
        "side_blocked",
        "long",
        None,
        "bullish->bearish",
        "The new evidence contradicts the committed thesis.",
    )
    values = compile_constraint(
        candidate,
        constraint_id="SC-001",
        symbol="SOL",
        decision={"id": "DEC-001"},
        t0={"as_of": "2026-09-08T01:00:00Z", "data": {"verdict": "bullish"}},
        t1={"as_of": "2026-09-08T01:01:00Z", "data": {"verdict": "bearish"}},
        t1_receipt_id="rcpt-002",
    )
    assert values["trigger_receipt_id"] == "rcpt-002"
