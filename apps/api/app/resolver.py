from __future__ import annotations

from .gate import GateResult, check_action


def resolve_action(action: dict, constraints: list[dict]) -> GateResult:
    """The single deterministic entry point used by every action path."""
    return check_action(action, [item for item in constraints if item.get("active")])

