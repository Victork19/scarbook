from __future__ import annotations

import asyncio
import json
from typing import Any

import httpx

from .config import Settings, settings
from .schemas import AgentDecision


SYSTEM_PROMPT = """You are the Scarbook practice-trading agent.
You receive current RYO evidence. Produce JSON with thesis, side (long/short/none), size (0, 0.25, or 1), confidence (0..1), and evidence_used.
Distinguish evidence from inference. Never claim unavailable data is available. This is a practice trade only, not execution.
"""


class AgentService:
    def __init__(self, app_settings: Settings = settings):
        self.settings = app_settings

    async def propose(self, evidence: dict[str, Any], constraints: list[dict[str, Any]] | None = None) -> tuple[AgentDecision, str]:
        if self.settings.llm_provider and self.settings.llm_api_key and self.settings.llm_model:
            decision = await self._llm_decide(evidence)
            if decision:
                return decision, "llm"
        return self._deterministic_decide(evidence), "deterministic fallback"

    def _deterministic_decide(self, evidence: dict[str, Any]) -> AgentDecision:
        data = evidence.get("data") or {}
        verdict = data.get("verdict")
        if verdict in {"bearish", "strong_bearish", "sell", "negative"}:
            side = "short"
            thesis = "Bearish evidence weakens the case for a long practice position."
        elif verdict in {"bullish", "strong_bullish", "buy", "positive"}:
            side = "long"
            thesis = "Bullish momentum and the current risk profile support a long practice position."
        else:
            side = "none"
            thesis = "The evidence does not support a directional practice position."
        return AgentDecision(
            thesis=thesis,
            side=side,
            size=1.0 if side != "none" else 0.0,
            confidence=0.72 if side != "none" else 0.5,
            evidence_used=[evidence.get("evidence_hash", evidence.get("as_of", "current"))],
        )

    async def _llm_decide(self, evidence: dict[str, Any]) -> AgentDecision | None:
        endpoint = self.settings.llm_provider.rstrip("/") + "/chat/completions"
        body = {
            "model": self.settings.llm_model,
            "temperature": 0,
            "max_completion_tokens": 512,
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "scarbook_agent_decision",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "thesis": {"type": "string", "minLength": 1, "maxLength": 1000},
                            "side": {"type": "string", "enum": ["long", "short", "none"]},
                            "size": {"type": "number", "enum": [0, 0.25, 1]},
                            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                            "evidence_used": {"type": "array", "items": {"type": "string"}},
                        },
                        "required": ["thesis", "side", "size", "confidence", "evidence_used"],
                    },
                },
            },
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(evidence, ensure_ascii=False)},
            ],
        }
        for attempt in range(3):
            try:
                async with httpx.AsyncClient(timeout=20) as client:
                    response = await client.post(endpoint, json=body, headers={"Authorization": f"Bearer {self.settings.llm_api_key}"})
                response.raise_for_status()
                content = response.json()["choices"][0]["message"]["content"]
                return AgentDecision.model_validate_json(content)
            except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError):
                if attempt < 2:
                    await asyncio.sleep(0.4 * (2**attempt))
        return None

    async def replan(self, evidence: dict[str, Any], blocked_decision: dict[str, Any], gate: dict[str, Any]) -> AgentDecision:
        """Replanning is intentionally bounded and deterministic when no LLM is configured."""
        if gate.get("reason") == "size_cap" and blocked_decision.get("side") in {"long", "short"}:
            return AgentDecision(
                thesis="Risk escalated, so the practice position is reduced to the permitted cap.",
                side=blocked_decision["side"],
                size=0.25,
                confidence=0.55,
                evidence_used=[evidence.get("evidence_hash", evidence.get("as_of", "current"))],
            )
        return AgentDecision(
            thesis="The preferred action is blocked by an evidence-bound constraint; preserve capital and take no new position.",
            side="none",
            size=0,
            confidence=0.9,
            evidence_used=[evidence.get("evidence_hash", evidence.get("as_of", "current"))],
        )
