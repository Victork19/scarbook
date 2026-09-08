from app.gate import check_action


def constraint(ctype, **kwargs):
    return {"id": kwargs.pop("id", "SC-001"), "constraint_type": ctype, "citation": "evidence citation", "active": True, **kwargs}


def test_side_blocked_rejects_long():
    result = check_action({"side": "long", "size": 1}, [constraint("side_blocked", blocked_side="long")])
    assert result.allowed is False
    assert result.effective_action is None


def test_size_cap_reduces_but_allows():
    result = check_action({"side": "long", "size": 1}, [constraint("size_cap", max_size=0.25)])
    assert result.allowed is True
    assert result.modified is True
    assert result.effective_action["size"] == 0.25


def test_inactive_constraint_does_not_block():
    result = check_action({"side": "long", "size": 1}, [constraint("no_new_position", active=False)])
    assert result.allowed is True
