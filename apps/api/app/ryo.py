from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

import httpx

from .config import Settings, settings
from .normalize import normalize_response
from .schemas import NormalizedEvidence


@dataclass
class RyoResponse:
    evidence: NormalizedEvidence
    raw: dict[str, Any]


class RyoClient:
    def __init__(self, app_settings: Settings = settings):
        self.settings = app_settings
        self.fixture_dir = Path(__file__).resolve().parents[1] / "fixtures"

    async def call_ryo(self, tool: str, payload: dict[str, Any]) -> RyoResponse:
        symbol = str(payload.get("symbol", "SOL")).upper()
        phase = payload.get("phase", "t0")
        if self.settings.fixtures:
            fixture_name = {"t0": "bullish", "t1": "bearish", "t2": "bullish"}.get(str(phase), "bullish")
            path = self.fixture_dir / f"{fixture_name}.json"
            raw = json.loads(path.read_text(encoding="utf-8"))
            evidence = normalize_response(raw, symbol=symbol, tool=tool, data_mode="fixture")
            return RyoResponse(evidence=evidence, raw=raw)

        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        if self.settings.ryo_mcp_key:
            headers["Authorization"] = f"Bearer {self.settings.ryo_mcp_key}"
        body = {"tool": tool, "arguments": {k: v for k, v in payload.items() if k != "phase"}}
        last_error: Exception | None = None
        for attempt in range(2):
            try:
                async with httpx.AsyncClient(timeout=15, headers=headers) as client:
                    response = await client.post(self.settings.ryo_mcp_url, json=body)
                if response.status_code in {429, 503, 504} and attempt == 0:
                    await asyncio.sleep(0.2)
                    continue
                response.raise_for_status()
                raw = response.json()
                evidence = normalize_response(raw, symbol=symbol, tool=tool, data_mode="live")
                if evidence.data_mode == "fixture":
                    evidence = evidence.model_copy(update={
                        "status": "error",
                        "data_mode": "error",
                        "warnings": [*evidence.warnings, "Fixture payload rejected in live mode"],
                    })
                return RyoResponse(evidence=evidence, raw=raw)
            except (httpx.HTTPError, ValueError, json.JSONDecodeError) as exc:
                last_error = exc
                if attempt == 0 and isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code in {429, 503, 504}:
                    await asyncio.sleep(0.2)
                    continue
                break
        message = f"RYO unavailable: {last_error}" if last_error else "RYO unavailable"
        raw = {"status": "error", "error": message}
        evidence = normalize_response(
            raw,
            symbol=symbol,
            tool=tool,
            data_mode="unavailable",
            default_status="error",
        )
        return RyoResponse(evidence=evidence, raw=raw)


_default_client = RyoClient()


async def call_ryo(tool: str, payload: dict[str, Any]) -> RyoResponse:
    """Stable adapter function for callers that do not need a client instance."""
    return await _default_client.call_ryo(tool, payload)
