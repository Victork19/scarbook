from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


Side = Literal["long", "short", "none"]
Phase = Literal["t0", "t1", "t2"]


class EvidenceData(BaseModel):
    verdict: str | None = None
    risk: str | None = None
    rsi14: float | None = None


class NormalizedEvidence(BaseModel):
    schema_version: str = "1.0"
    tool: str
    status: str
    data_mode: Literal["live", "fixture", "unavailable", "error"]
    as_of: datetime
    request: dict[str, Any] = Field(default_factory=dict)
    data: EvidenceData = Field(default_factory=EvidenceData)
    warnings: list[str] = Field(default_factory=list)


class AgentDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    thesis: str = Field(min_length=1, max_length=1000)
    side: Side
    size: float = Field(ge=0, le=1)
    confidence: float = Field(ge=0, le=1)
    evidence_used: list[str] = Field(default_factory=list)

    @field_validator("size")
    @classmethod
    def supported_size(cls, value: float) -> float:
        if value not in {0, 0.25, 1}:
            raise ValueError("size must be one of 0, 0.25, or 1")
        return value


class Action(BaseModel):
    side: Side
    size: float = Field(ge=0, le=1)

    @field_validator("size")
    @classmethod
    def supported_size(cls, value: float) -> float:
        if value not in {0, 0.25, 1}:
            raise ValueError("size must be one of 0, 0.25, or 1")
        return value


class StartRequest(BaseModel):
    symbol: str = Field(min_length=1, max_length=20)

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, value: str) -> str:
        return value.strip().upper()


class CommitRequest(BaseModel):
    session_id: str
    decision: AgentDecision


class SessionRequest(BaseModel):
    symbol: str = Field(min_length=1, max_length=20)
    parent_session_id: str | None = None

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, value: str) -> str:
        return value.strip().upper()


class RecheckRequest(BaseModel):
    session_id: str


class ActionCheckRequest(BaseModel):
    symbol: str = Field(min_length=1, max_length=20)
    action: Action

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, value: str) -> str:
        return value.strip().upper()


class WipeRequest(BaseModel):
    symbol: str = Field(min_length=1, max_length=20)

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, value: str) -> str:
        return value.strip().upper()

