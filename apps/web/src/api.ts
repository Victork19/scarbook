import type { EvidenceDelta, Health, NewSessionResponse, RecheckResponse, SessionResponse } from "./types";

const API_BASE = (import.meta.env.VITE_API_URL as string | undefined) || "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = typeof body.detail === "string" ? body.detail : body.detail?.message || "Request failed";
    throw new Error(detail);
  }
  return body as T;
}

export const api = {
  health: () => request<Health>("/health"),
  start: (symbol: string) => request<SessionResponse>("/api/session", { method: "POST", body: JSON.stringify({ symbol }) }),
  commit: (sessionId: string, decision: Record<string, unknown>) =>
    request<{ decision_id: string }>("/api/decision/commit", { method: "POST", body: JSON.stringify({ session_id: sessionId, decision }) }),
  recheck: (sessionId: string) => request<RecheckResponse>("/api/recheck", { method: "POST", body: JSON.stringify({ session_id: sessionId }) }),
  freshSession: (symbol: string, parentSessionId: string) =>
    request<NewSessionResponse>("/api/session/new", { method: "POST", body: JSON.stringify({ symbol, parent_session_id: parentSessionId }) }),
  evidenceDelta: (symbol: string) => request<EvidenceDelta>("/api/skill/evidence-delta", { method: "POST", body: JSON.stringify({ symbol }) }),
  wipe: (symbol: string) => request<{ constraints: import("./types").Constraint[] }>("/api/wipe", { method: "POST", body: JSON.stringify({ symbol }) }),
};
