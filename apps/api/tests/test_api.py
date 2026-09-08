"""Contract tests for the most important gate response shape.

The full live API test is intentionally kept separate from external RYO availability.
"""

from app.gate import check_action


def test_blocked_action_never_has_effective_action():
    result = check_action({"side": "long", "size": 1}, [{
        "id": "SC-001", "constraint_type": "no_new_position", "citation": "T1 unavailable", "active": True,
    }])
    payload = result.as_dict()
    assert payload["allowed"] is False
    assert payload["effective_action"] is None
