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


def _decode_mcp_response(raw: dict[str, Any]) -> dict[str, Any]:
    """Convert an MCP JSON-RPC response into the payload normalizer expects."""
    if not isinstance(raw, dict) or raw.get("jsonrpc") != "2.0":
        return raw

    if raw.get("error"):
        error = raw["error"]
        message = error.get("message", "MCP request failed") if isinstance(error, dict) else str(error)
        return {
            "status": "error",
            "data_mode": "unavailable",
            "error": message,
            "warnings": [message],
        }

    result = raw.get("result")
    if not isinstance(result, dict):
        return {"status": "error", "data_mode": "error", "warnings": ["MCP response had no result"]}

    structured = result.get("structuredContent")
    if isinstance(structured, dict):
        return structured

    for item in result.get("content", []):
        if not isinstance(item, dict) or item.get("type") != "text":
            continue
        text = item.get("text")
        if not isinstance(text, str):
            continue
        try:
            decoded = json.loads(text)
        except json.JSONDecodeError:
            return {"status": "ok", "data": {"summary": text}}
        if isinstance(decoded, dict):
            return decoded

    return {"status": "ok", "data": result}


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
        body = {
            "jsonrpc": "2.0",
            "id": f"scarbook-{tool}",
            "method": "tools/call",
            "params": {
                "name": tool,
                "arguments": {k: v for k, v in payload.items() if k != "phase"},
            },
        }
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
                decoded = _decode_mcp_response(raw)
                evidence = normalize_response(decoded, symbol=symbol, tool=tool, data_mode="live")
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
