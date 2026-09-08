from __future__ import annotations

import json
from pathlib import Path
import sqlite3
from typing import Any

from .config import Settings, settings
from .utils import now_iso, public_id


SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS sessions (
  id TEXT PRIMARY KEY,
  symbol TEXT NOT NULL,
  created_at TEXT NOT NULL,
  parent_session_id TEXT,
  status TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS evidence_receipts (
  id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL REFERENCES sessions(id),
  symbol TEXT NOT NULL,
  phase TEXT NOT NULL CHECK (phase IN ('t0','t1','t2')),
  tool TEXT NOT NULL,
  as_of TEXT NOT NULL,
  status TEXT NOT NULL,
  data_mode TEXT NOT NULL,
  evidence_json TEXT NOT NULL,
  evidence_hash TEXT NOT NULL,
  raw_path TEXT,
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_receipts_session_phase ON evidence_receipts(session_id, phase);
CREATE TABLE IF NOT EXISTS decisions (
  id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL REFERENCES sessions(id),
  receipt_id TEXT NOT NULL REFERENCES evidence_receipts(id),
  symbol TEXT NOT NULL,
  side TEXT NOT NULL,
  size REAL NOT NULL,
  thesis TEXT NOT NULL,
  confidence REAL NOT NULL,
  evidence_used_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS constraints (
  id TEXT PRIMARY KEY,
  symbol TEXT NOT NULL,
  source_decision_id TEXT NOT NULL REFERENCES decisions(id),
  trigger_receipt_id TEXT NOT NULL REFERENCES evidence_receipts(id),
  class TEXT NOT NULL,
  constraint_type TEXT NOT NULL,
  parameter TEXT,
  blocked_side TEXT,
  max_size REAL,
  reason TEXT NOT NULL,
  citation TEXT NOT NULL,
  action_policy_json TEXT NOT NULL,
  active INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL,
  UNIQUE(symbol, source_decision_id, trigger_receipt_id)
);
"""


class Database:
    def __init__(self, app_settings: Settings = settings, path: str | None = None):
        self.path = str(path or app_settings.database_path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        Path(app_settings.raw_dir).mkdir(parents=True, exist_ok=True)
        self.initialize()

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        return connection

    def initialize(self) -> None:
        with self.connect() as connection:
            connection.executescript(SCHEMA)

    @staticmethod
    def _dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
        return dict(row) if row else None

    def _next_id(self, connection: sqlite3.Connection, table: str, prefix: str) -> str:
        row = connection.execute(f"SELECT COUNT(*) AS count FROM {table}").fetchone()
        return public_id(prefix, int(row["count"]) + 1)

    def next_constraint_id(self) -> str:
        with self.connect() as connection:
            return self._next_id(connection, "constraints", "SC")

    def create_session(self, symbol: str, parent_session_id: str | None = None) -> dict[str, Any]:
        with self.connect() as connection:
            session_id = self._next_id(connection, "sessions", "sess")
            connection.execute(
                "INSERT INTO sessions(id,symbol,created_at,parent_session_id,status) VALUES(?,?,?,?,?)",
                (session_id, symbol, now_iso(), parent_session_id, "session_started"),
            )
        return self.get_session(session_id)  # type: ignore[return-value]

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        with self.connect() as connection:
            return self._dict(connection.execute("SELECT * FROM sessions WHERE id=?", (session_id,)).fetchone())

    def update_session(self, session_id: str, status: str) -> None:
        with self.connect() as connection:
            connection.execute("UPDATE sessions SET status=? WHERE id=?", (status, session_id))

    def create_receipt(
        self,
        *,
        session_id: str,
        symbol: str,
        phase: str,
        evidence: dict[str, Any],
        evidence_hash: str,
        raw_path: str | None = None,
    ) -> dict[str, Any]:
        with self.connect() as connection:
            receipt_id = self._next_id(connection, "evidence_receipts", "rcpt")
            connection.execute(
                """INSERT INTO evidence_receipts
                (id,session_id,symbol,phase,tool,as_of,status,data_mode,evidence_json,evidence_hash,raw_path,created_at)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    receipt_id,
                    session_id,
                    symbol,
                    phase,
                    evidence["tool"],
                    evidence["as_of"],
                    evidence["status"],
                    evidence["data_mode"],
                    json.dumps(evidence, ensure_ascii=False),
                    evidence_hash,
                    raw_path,
                    now_iso(),
                ),
            )
        return self.get_receipt(receipt_id)  # type: ignore[return-value]

    def get_receipt(self, receipt_id: str) -> dict[str, Any] | None:
        with self.connect() as connection:
            row = self._dict(connection.execute("SELECT * FROM evidence_receipts WHERE id=?", (receipt_id,)).fetchone())
        if row:
            row["evidence"] = json.loads(row.pop("evidence_json"))
        return row

    def get_receipt_for_phase(self, session_id: str, phase: str) -> dict[str, Any] | None:
        with self.connect() as connection:
            row = self._dict(
                connection.execute(
                    "SELECT * FROM evidence_receipts WHERE session_id=? AND phase=? ORDER BY created_at DESC LIMIT 1",
                    (session_id, phase),
                ).fetchone()
            )
        if row:
            row["evidence"] = json.loads(row.pop("evidence_json"))
        return row

    def update_receipt_raw_path(self, receipt_id: str, raw_path: str) -> None:
        with self.connect() as connection:
            connection.execute("UPDATE evidence_receipts SET raw_path=? WHERE id=?", (raw_path, receipt_id))

    def create_decision(self, *, session_id: str, receipt_id: str, decision: dict[str, Any]) -> dict[str, Any]:
        with self.connect() as connection:
            decision_id = self._next_id(connection, "decisions", "DEC")
            connection.execute(
                """INSERT INTO decisions
                (id,session_id,receipt_id,symbol,side,size,thesis,confidence,evidence_used_json,created_at)
                VALUES(?,?,?,?,?,?,?,?,?,?)""",
                (
                    decision_id,
                    session_id,
                    receipt_id,
                    decision["symbol"],
                    decision["side"],
                    decision["size"],
                    decision["thesis"],
                    decision["confidence"],
                    json.dumps(decision.get("evidence_used", [])),
                    now_iso(),
                ),
            )
        return self.get_decision(decision_id)  # type: ignore[return-value]

    def get_decision(self, decision_id: str) -> dict[str, Any] | None:
        with self.connect() as connection:
            row = self._dict(connection.execute("SELECT * FROM decisions WHERE id=?", (decision_id,)).fetchone())
        if row:
            row["evidence_used"] = json.loads(row.pop("evidence_used_json"))
        return row

    def get_decision_for_session(self, session_id: str) -> dict[str, Any] | None:
        with self.connect() as connection:
            row = self._dict(
                connection.execute("SELECT * FROM decisions WHERE session_id=? ORDER BY created_at DESC LIMIT 1", (session_id,)).fetchone()
            )
        if row:
            row["evidence_used"] = json.loads(row.pop("evidence_used_json"))
        return row

    def create_constraint(self, values: dict[str, Any]) -> dict[str, Any]:
        with self.connect() as connection:
            existing = connection.execute(
                "SELECT * FROM constraints WHERE symbol=? AND source_decision_id=? AND trigger_receipt_id=?",
                (values["symbol"], values["source_decision_id"], values["trigger_receipt_id"]),
            ).fetchone()
            if existing:
                return self._constraint_dict(existing)
            constraint_id = self._next_id(connection, "constraints", "SC")
            connection.execute(
                """INSERT INTO constraints
                (id,symbol,source_decision_id,trigger_receipt_id,class,constraint_type,parameter,blocked_side,max_size,reason,citation,action_policy_json,active,created_at)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    constraint_id,
                    values["symbol"],
                    values["source_decision_id"],
                    values["trigger_receipt_id"],
                    values["class"],
                    values["constraint"],
                    values.get("parameter"),
                    values.get("blocked_side"),
                    values.get("max_size"),
                    values["reason"],
                    values["citation"],
                    json.dumps(values["action_policy"]),
                    1,
                    now_iso(),
                ),
            )
            row = connection.execute("SELECT * FROM constraints WHERE id=?", (constraint_id,)).fetchone()
            return self._constraint_dict(row)  # type: ignore[arg-type]

    @staticmethod
    def _constraint_dict(row: sqlite3.Row) -> dict[str, Any]:
        value = dict(row)
        value["active"] = bool(value["active"])
        value["constraint"] = value["constraint_type"]
        value["action_policy"] = json.loads(value.pop("action_policy_json"))
        return value

    def constraints(self, symbol: str, active_only: bool = False) -> list[dict[str, Any]]:
        query = "SELECT * FROM constraints WHERE symbol=?"
        args: list[Any] = [symbol]
        if active_only:
            query += " AND active=1"
        query += " ORDER BY created_at ASC"
        with self.connect() as connection:
            rows = connection.execute(query, args).fetchall()
        return [self._constraint_dict(row) for row in rows]

    def deactivate_constraints(self, symbol: str) -> int:
        with self.connect() as connection:
            cursor = connection.execute("UPDATE constraints SET active=0 WHERE symbol=? AND active=1", (symbol,))
            return cursor.rowcount

    def latest_session(self, symbol: str | None = None) -> dict[str, Any] | None:
        with self.connect() as connection:
            if symbol:
                row = connection.execute("SELECT * FROM sessions WHERE symbol=? ORDER BY created_at DESC LIMIT 1", (symbol,)).fetchone()
            else:
                row = connection.execute("SELECT * FROM sessions ORDER BY created_at DESC LIMIT 1").fetchone()
        return self._dict(row)
