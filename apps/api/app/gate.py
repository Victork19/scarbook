from __future__ import annotations

from dataclasses import dataclass
from typing import Any


PRIORITY = {"no_new_position": 3, "side_blocked": 2, "size_cap": 1}


@dataclass(frozen=True)
class GateResult:
    allowed: bool
    effective_action: dict[str, Any] | None
    reason: str | None
    constraint_ids: list[str]
    citation: str | None
    modified: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "allowed": self.allowed,
            "effective_action": self.effective_action,
            "reason": self.reason,
            "constraint_ids": self.constraint_ids,
            "citation": self.citation,
            "modified": self.modified,
        }


def check_action(action: dict[str, Any], constraints: list[dict[str, Any]]) -> GateResult:
    active = sorted(
        (item for item in constraints if item.get("active", True)),
        key=lambda item: PRIORITY.get(item["constraint_type"], 0),
        reverse=True,
    )
    if action["side"] == "none" or action["size"] == 0:
        return GateResult(True, {"side": "none", "size": 0}, None, [], None)
    for constraint in active:
        ctype = constraint["constraint_type"]
        if ctype == "no_new_position":
            return GateResult(False, None, ctype, [constraint["id"]], constraint["citation"])
        if ctype == "side_blocked" and action["side"] == constraint.get("blocked_side"):
            return GateResult(False, None, ctype, [constraint["id"]], constraint["citation"])
    caps = [item for item in active if item["constraint_type"] == "size_cap" and item.get("max_size") is not None]
    if caps:
        cap = min(float(item["max_size"]) for item in caps)
        if action["size"] > cap:
            winner = caps[0]
            return GateResult(
                True,
                {"side": action["side"], "size": cap},
                "size_cap",
                [item["id"] for item in caps],
                winner["citation"],
                modified=True,
            )
    return GateResult(True, action, None, [], None)
