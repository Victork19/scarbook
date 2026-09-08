export type Side = "long" | "short" | "none";

export interface EvidenceData {
  verdict?: string | null;
  risk?: string | null;
  rsi14?: number | null;
}

export interface Receipt {
  id: string;
  session_id: string;
  symbol: string;
  phase: "t0" | "t1" | "t2";
  tool: string;
  as_of: string;
  status: string;
  data_mode: string;
  evidence: { data: EvidenceData; [key: string]: unknown };
  evidence_hash: string;
  hash_short: string;
}

export interface Decision {
  thesis: string;
  side: Side;
  size: number;
  confidence: number;
  evidence_used: string[];
  agent_mode?: string;
}

export interface Constraint {
  id: string;
  symbol: string;
  class: string;
  constraint?: "side_blocked" | "size_cap" | "no_new_position";
  constraint_type: "side_blocked" | "size_cap" | "no_new_position";
  blocked_side?: Side | null;
  max_size?: number | null;
  reason: string;
  citation: string;
  active: boolean;
  source_decision_id: string;
  trigger_receipt_id: string;
}

export interface SessionResponse {
  session_id: string;
  session: { id: string; symbol: string; status: string; parent_session_id?: string | null };
  receipt: Receipt;
  proposal: Decision;
}

export interface RecheckResponse {
  session_id: string;
  t0: Receipt;
  t1: Receipt;
  contradiction: boolean;
  constraint?: Constraint | null;
  active_constraints: Constraint[];
}

export interface Gate {
  allowed: boolean;
  effective_action: { side: Side; size: number } | null;
  original_action?: { side: Side; size: number };
  reason?: string | null;
  constraint_ids: string[];
  citation?: string | null;
  modified?: boolean;
}

export interface NewSessionResponse {
  session_id: string;
  session: { id: string; symbol: string; status: string; parent_session_id?: string | null };
  receipt: Receipt;
  proposal: Decision;
  gate: Gate;
  final_decision: Decision;
  replanned: boolean;
  active_constraints: Constraint[];
}

export interface Health {
  live: boolean;
  fixtures: boolean;
  ryo_reachable: boolean;
  llm_configured: boolean;
}
