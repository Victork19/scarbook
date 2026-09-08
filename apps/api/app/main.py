from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .agent import AgentService
from .config import settings
from .constraints import compile_constraint
from .contradiction import detect_contradiction
from .db import Database
from .evidence_delta import EVIDENCE_DELTA_TOOL, compare_evidence
from .gate import check_action
from .hashing import evidence_hash
from .resolver import resolve_action
from .ryo import RyoClient
from .schemas import ActionCheckRequest, CommitRequest, EvidenceDeltaRequest, RecheckRequest, SessionRequest, StartRequest, WipeRequest
from .utils import safe_symbol


app = FastAPI(title="Scarbook API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)

db = Database()
ryo = RyoClient()
agent = AgentService()


def _receipt_response(receipt: dict[str, Any] | None) -> dict[str, Any] | None:
    if not receipt:
        return None
    evidence = receipt.get("evidence", {})
    return {
        "id": receipt["id"],
        "session_id": receipt["session_id"],
        "symbol": receipt["symbol"],
        "phase": receipt["phase"],
        "tool": receipt["tool"],
        "as_of": receipt["as_of"],
        "status": receipt["status"],
        "data_mode": receipt["data_mode"],
        "evidence": evidence,
        "evidence_hash": receipt["evidence_hash"],
        "hash_short": receipt["evidence_hash"][:8].upper(),
        "raw_path": receipt.get("raw_path"),
    }


def _decision_response(decision: dict[str, Any] | Any, *, mode: str | None = None) -> dict[str, Any]:
    if hasattr(decision, "model_dump"):
        result = decision.model_dump()
    else:
        result = dict(decision)
    result.pop("symbol", None)
    if mode:
        result["agent_mode"] = mode
    return result


def _save_raw(receipt_id: str, raw: dict[str, Any]) -> str:
    raw_dir = Path(settings.raw_dir)
    raw_dir.mkdir(parents=True, exist_ok=True)
    path = raw_dir / f"{receipt_id}.json"
    path.write_text(json.dumps(raw, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return str(path)


async def _observe(session_id: str, symbol: str, phase: str) -> dict[str, Any]:
    response = await ryo.call_ryo("analyze_token", {"symbol": symbol, "phase": phase})
    evidence = response.evidence.model_dump(mode="json")
    digest = evidence_hash(evidence)
    receipt = db.create_receipt(
        session_id=session_id,
        symbol=symbol,
        phase=phase,
        evidence=evidence,
        evidence_hash=digest,
    )
    raw_path = _save_raw(receipt["id"], response.raw)
    db.update_receipt_raw_path(receipt["id"], raw_path)
    receipt["raw_path"] = raw_path
    return receipt


def _require_session(session_id: str) -> dict[str, Any]:
    session = db.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@app.get("/health")
async def health() -> dict[str, Any]:
    fixtures = settings.fixtures
    configured = bool(settings.ryo_mcp_url)
    return {
        "live": bool(not fixtures and configured),
        "fixtures": fixtures,
        "ryo_reachable": bool(fixtures or configured),
        "llm_configured": bool(settings.llm_provider and settings.llm_api_key and settings.llm_model),
    }


async def _evidence_delta(symbol: str) -> dict[str, Any]:
    before = await ryo.call_ryo("analyze_token", {"symbol": symbol, "phase": "t0"})
    after = await ryo.call_ryo("analyze_token", {"symbol": symbol, "phase": "t1"})
    return compare_evidence(
        symbol,
        before.evidence.model_dump(mode="json"),
        after.evidence.model_dump(mode="json"),
    )


@app.post("/api/skill/evidence-delta")
async def evidence_delta(request: EvidenceDeltaRequest) -> dict[str, Any]:
    return await _evidence_delta(request.symbol)


@app.post("/api/mcp")
async def skill_mcp(request: dict[str, Any]) -> dict[str, Any]:
    """Minimal JSON-RPC MCP surface for the Track 3 read-only skill."""
    request_id = request.get("id")
    method = request.get("method")
    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "scarbook-skills", "version": "1.0.0"},
            },
        }
    if method == "notifications/initialized":
        return {"jsonrpc": "2.0", "id": request_id, "result": {}}
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": request_id, "result": {"tools": [EVIDENCE_DELTA_TOOL]}}
    if method != "tools/call":
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {"code": -32601, "message": f"Unsupported method: {method}"},
        }

    params = request.get("params") or {}
    if params.get("name") != EVIDENCE_DELTA_TOOL["name"]:
        return {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32602, "message": "Unknown tool"}}
    try:
        arguments = EvidenceDeltaRequest.model_validate(params.get("arguments") or {})
    except Exception as exc:
        return {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32602, "message": str(exc)}}
    result = await _evidence_delta(arguments.symbol)
    encoded = json.dumps(result, ensure_ascii=False, separators=(",", ":"))
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": {
            "content": [{"type": "text", "text": encoded}],
            "structuredContent": result,
            "isError": False,
        },
    }


@app.post("/api/session")
@app.post("/api/session/start")
async def start_session(request: StartRequest) -> dict[str, Any]:
    symbol = safe_symbol(request.symbol)
    if not symbol:
        raise HTTPException(status_code=400, detail="A valid symbol is required")
    session = db.create_session(symbol)
    receipt = await _observe(session["id"], symbol, "t0")
    if receipt["status"] != "ok" or receipt["data_mode"] not in {"live", "fixture"}:
        db.update_session(session["id"], "t0_unavailable")
        raise HTTPException(status_code=503, detail={"message": "RYO unavailable", "receipt": _receipt_response(receipt)})
    proposal, mode = await agent.propose(receipt["evidence"])
    db.update_session(session["id"], "decision_proposed")
    return {
        "session": db.get_session(session["id"]),
        "session_id": session["id"],
        "receipt": _receipt_response(receipt),
        "evidence": receipt["evidence"]["data"],
        "proposal": _decision_response(proposal, mode=mode),
    }


@app.post("/api/decision/commit")
async def commit_decision(request: CommitRequest) -> dict[str, Any]:
    session = _require_session(request.session_id)
    receipt = db.get_receipt_for_phase(request.session_id, "t0")
    if not receipt:
        raise HTTPException(status_code=409, detail="No T0 evidence exists")
    if receipt["status"] != "ok" or receipt["data_mode"] not in {"live", "fixture"}:
        raise HTTPException(status_code=409, detail="RYO unavailable; no decision committed")
    existing = db.get_decision_for_session(request.session_id)
    if existing:
        return {"session": session, "decision_id": existing["id"], "decision": _decision_response(existing), "receipt": _receipt_response(receipt), "idempotent": True}
    values = request.decision.model_dump()
    values["symbol"] = session["symbol"]
    decision = db.create_decision(session_id=session["id"], receipt_id=receipt["id"], decision=values)
    db.update_session(session["id"], "committed")
    return {"session": db.get_session(session["id"]), "decision_id": decision["id"], "decision": _decision_response(decision), "receipt": _receipt_response(receipt)}


def _recheck_response(session: dict[str, Any], t1: dict[str, Any], constraint: dict[str, Any] | None) -> dict[str, Any]:
    t0 = db.get_receipt_for_phase(session["id"], "t0")
    return {
        "session": db.get_session(session["id"]),
        "session_id": session["id"],
        "t0": _receipt_response(t0),
        "t1": _receipt_response(t1),
        "contradiction": constraint is not None,
        "constraint": constraint,
        "active_constraints": db.constraints(session["symbol"], active_only=True),
    }


@app.post("/api/recheck")
async def recheck(request: RecheckRequest) -> dict[str, Any]:
    session = _require_session(request.session_id)
    decision = db.get_decision_for_session(request.session_id)
    if not decision:
        raise HTTPException(status_code=409, detail="Commit a decision before rechecking")
    existing_t1 = db.get_receipt_for_phase(request.session_id, "t1")
    if existing_t1:
        existing = db.constraints(session["symbol"], active_only=False)
        constraint = next((item for item in existing if item["trigger_receipt_id"] == existing_t1["id"]), None)
        return _recheck_response(session, existing_t1, constraint)
    t1 = await _observe(session["id"], session["symbol"], "t1")
    candidate = detect_contradiction(db.get_receipt_for_phase(session["id"], "t0")["evidence"], t1["evidence"], decision)
    constraint = None
    if candidate:
        constraint_id = db.next_constraint_id()
        values = compile_constraint(
            candidate,
            constraint_id=constraint_id,
            symbol=session["symbol"],
            decision=decision,
            t0=db.get_receipt_for_phase(session["id"], "t0")["evidence"],
            t1=t1["evidence"],
            t1_receipt_id=t1["id"],
        )
        constraint = db.create_constraint(values)
        db.update_session(session["id"], "constraint_active")
    else:
        db.update_session(session["id"], "contradiction_checked")
    return _recheck_response(session, t1, constraint)


@app.post("/api/action/check")
async def action_check(request: ActionCheckRequest) -> dict[str, Any]:
    constraints = db.constraints(safe_symbol(request.symbol), active_only=True)
    result = resolve_action(request.action.model_dump(), constraints)
    return result.as_dict()


@app.post("/api/session/new")
async def new_session(request: SessionRequest) -> dict[str, Any]:
    symbol = safe_symbol(request.symbol)
    if not symbol:
        raise HTTPException(status_code=400, detail="A valid symbol is required")
    parent = db.get_session(request.parent_session_id) if request.parent_session_id else None
    session = db.create_session(symbol, parent_session_id=parent["id"] if parent else None)
    t2 = await _observe(session["id"], symbol, "t2")
    constraints = db.constraints(symbol, active_only=True)
    proposal, mode = await agent.propose(t2["evidence"], constraints)
    proposed = {"side": proposal.side, "size": proposal.size}
    first_gate = check_action(proposed, constraints)
    replanned = False
    final_decision = proposal
    gate = first_gate
    if not first_gate.allowed:
        replanned = True
        final_decision = await agent.replan(t2["evidence"], proposal.model_dump(), first_gate.as_dict())
        gate = check_action({"side": final_decision.side, "size": final_decision.size}, constraints)
        if not gate.allowed:
            raise HTTPException(status_code=500, detail="Replanning produced an action that failed the gate")
    db.update_session(session["id"], "final_decision")
    return {
        "session": db.get_session(session["id"]),
        "session_id": session["id"],
        "receipt": _receipt_response(t2),
        "proposal": _decision_response(proposal, mode=mode),
        "gate": {**gate.as_dict(), "original_action": proposed},
        "final_decision": _decision_response(final_decision, mode=mode),
        "replanned": replanned,
        "active_constraints": constraints,
    }


@app.post("/api/wipe")
async def wipe(request: WipeRequest) -> dict[str, Any]:
    symbol = safe_symbol(request.symbol)
    count = db.deactivate_constraints(symbol)
    return {"symbol": symbol, "deactivated": count, "constraints": db.constraints(symbol, active_only=False)}


@app.get("/api/constraints/{symbol}")
async def constraints(symbol: str, active: bool = Query(False)) -> dict[str, Any]:
    return {"symbol": safe_symbol(symbol), "constraints": db.constraints(safe_symbol(symbol), active_only=active)}


@app.get("/api/sessions/{session_id}")
async def session_detail(session_id: str) -> dict[str, Any]:
    session = _require_session(session_id)
    receipts = []
    for phase in ("t0", "t1", "t2"):
        receipt = db.get_receipt_for_phase(session_id, phase)
        if receipt:
            receipts.append(_receipt_response(receipt))
    return {"session": session, "receipts": receipts, "decision": db.get_decision_for_session(session_id)}


@app.get("/api/state")
async def state(symbol: str | None = None) -> dict[str, Any]:
    symbol = safe_symbol(symbol) if symbol else None
    latest = db.latest_session(symbol)
    resolved_symbol = symbol or (latest["symbol"] if latest else None)
    if not resolved_symbol:
        return {"symbol": None, "session_id": None, "active_constraints": [], "historical_constraints": [], "latest_decision": None}
    latest = db.latest_session(resolved_symbol)
    decision = db.get_decision_for_session(latest["id"]) if latest else None
    return {
        "symbol": resolved_symbol,
        "session_id": latest["id"] if latest else None,
        "active_constraints": db.constraints(resolved_symbol, active_only=True),
        "historical_constraints": db.constraints(resolved_symbol, active_only=False),
        "latest_decision": _decision_response(decision) if decision else None,
    }
