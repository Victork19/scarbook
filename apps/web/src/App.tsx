import { useEffect, useMemo, useState } from "react";
import { ArrowRight, Check, CircleAlert, CircleDot, GitBranch, LockKeyhole, RotateCcw, ShieldCheck, Sparkles, X } from "lucide-react";
import { api } from "./api";
import type { Constraint, Decision, EvidenceDelta, Health, NewSessionResponse, Receipt, RecheckResponse, SessionResponse } from "./types";

const initialHealth: Health = { live: false, fixtures: false, ryo_reachable: false, llm_configured: false };

function formatTime(value?: string) {
  if (!value) return "—";
  return new Date(value).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

function upper(value?: string | null) {
  return value ? value.toUpperCase() : "—";
}

function DecisionCard({ decision, label, muted = false }: { decision?: Decision | null; label: string; muted?: boolean }) {
  if (!decision) return null;
  return (
    <div className={`decision-card ${muted ? "muted" : ""}`}>
      <div className="eyebrow">{label}</div>
      <p className="thesis">“{decision.thesis}”</p>
      <div className="action-line"><span>{upper(decision.side)}</span><strong>{decision.size.toFixed(2)}</strong></div>
      <div className="confidence">Confidence {Math.round(decision.confidence * 100)}% {decision.agent_mode ? `· ${decision.agent_mode}` : ""}</div>
    </div>
  );
}

function Evidence({ receipt, title }: { receipt?: Receipt | null; title: string }) {
  if (!receipt) return null;
  const data = receipt.evidence.data || {};
  return (
    <div className="evidence-block">
      <div className="section-label"><span>{title}</span><span className="receipt-tag">{receipt.id}</span></div>
      <div className="metric-grid">
        <div><span>Verdict</span><b>{upper(data.verdict)}</b></div>
        <div><span>Risk</span><b>{upper(data.risk)}</b></div>
        <div><span>RSI14</span><b>{data.rsi14 ?? "—"}</b></div>
      </div>
      <div className="receipt-meta"><span>As of {formatTime(receipt.as_of)}</span><span className="hash">HASH {receipt.hash_short}</span></div>
    </div>
  );
}

function ConstraintCard({ constraint }: { constraint: Constraint }) {
  return (
    <div className={`constraint-card ${constraint.active ? "active" : "inactive"}`}>
      <div className="constraint-top"><span className="scar-id">{constraint.id}</span><span className="constraint-state">{constraint.active ? "ACTIVE" : "INACTIVE"}</span></div>
      <div className="constraint-title">{constraint.constraint_type === "side_blocked" ? `${upper(constraint.blocked_side)} BLOCKED` : constraint.constraint_type === "size_cap" ? `SIZE ≤ ${constraint.max_size}` : "NO NEW POSITION"}</div>
      <p>{constraint.citation}</p>
    </div>
  );
}

function EvidenceDeltaCard({ delta }: { delta?: EvidenceDelta | null }) {
  if (!delta) {
    return (
      <div className="skill-empty">
        <Sparkles size={22} />
        <p>Run the new read-only skill to compare<br />two sequential RYO observations.</p>
      </div>
    );
  }

  const before = delta.observations.find((item) => item.label === "before");
  const after = delta.observations.find((item) => item.label === "after");
  const state = delta.data.state.replaceAll("_", " ").toUpperCase();

  return (
    <div className="skill-result">
      <div className="skill-result-top">
        <div><span className="eyebrow">EVIDENCE DELTA RESULT</span><strong>{state}</strong></div>
        <span className={`skill-status ${delta.status}`}>{delta.status.toUpperCase()}</span>
      </div>
      <div className="delta-pair">
        {[before, after].map((observation) => observation && (
          <div className="delta-observation" key={observation.label}>
            <span className="delta-label">{observation.label === "before" ? "BEFORE / T0" : "AFTER / T1"}</span>
            <b>{upper(observation.data.verdict)}</b>
            <span>RSI14 {observation.data.rsi14 ?? "—"} · RISK {upper(observation.data.risk)}</span>
            <small>{formatTime(observation.as_of)} · HASH {observation.hash_short}</small>
          </div>
        ))}
      </div>
      {delta.data.transition && <div className="delta-transition"><span>TRANSITION</span><strong>{delta.data.transition}</strong></div>}
      {delta.data.changes.length > 0 ? <div className="delta-changes"><span>CHANGES DETECTED</span>{delta.data.changes.map((change) => <div key={change.field}><b>{change.field}</b><span>{String(change.before)} <ArrowRight size={13} /> {String(change.after)}</span></div>)}</div> : <div className="delta-unchanged">No compared fields changed between the two observations.</div>}
      <div className="skill-note">
        <ShieldCheck size={15} />
        {delta.warnings.length ? delta.warnings[0] : "No missing fields. The observations were compared without inference."}
      </div>
    </div>
  );
}

export default function App() {
  const [symbol, setSymbol] = useState("SOL");
  const [health, setHealth] = useState(initialHealth);
  const [session, setSession] = useState<SessionResponse | null>(null);
  const [commitId, setCommitId] = useState<string | null>(null);
  const [recheck, setRecheck] = useState<RecheckResponse | null>(null);
  const [fresh, setFresh] = useState<NewSessionResponse | null>(null);
  const [delta, setDelta] = useState<EvidenceDelta | null>(null);
  const [historical, setHistorical] = useState<Constraint[]>([]);
  const [loading, setLoading] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => { api.health().then(setHealth).catch((reason: Error) => setError(reason.message)); }, []);

  const activeConstraints = fresh?.active_constraints || recheck?.active_constraints || [];
  const currentRecheck = recheck as RecheckResponse;
  const currentFresh = fresh as NewSessionResponse;
  const hasT0 = Boolean(session);
  const hasCommit = Boolean(commitId);
  const hasT1 = Boolean(recheck);
  const hasFresh = Boolean(fresh);
  const statusText = useMemo(() => {
    if (hasFresh) return fresh?.replanned ? "REPLAN ACCEPTED" : fresh?.gate.allowed ? "DECISION READY" : "ACTION BLOCKED";
    if (hasT1) return recheck?.contradiction ? "CONSTRAINT ACTIVE" : "NO CONTRADICTION";
    if (hasCommit) return "COMMITTED";
    if (hasT0) return "DECISION PROPOSED";
    return "READY";
  }, [hasCommit, hasFresh, hasT0, hasT1, recheck?.contradiction]);

  async function run(label: string, action: () => Promise<void>) {
    setLoading(label); setError(null);
    try { await action(); } catch (reason) { setError(reason instanceof Error ? reason.message : "Request failed"); } finally { setLoading(null); }
  }

  function cleanDecision(decision: Decision) {
    const { agent_mode: _agentMode, ...payload } = decision;
    return payload;
  }

  function start() {
    run("start", async () => { setSession(await api.start(symbol)); setCommitId(null); setRecheck(null); setFresh(null); setDelta(null); setHistorical([]); });
  }

  function commit() {
    if (!session) return;
    run("commit", async () => { const result = await api.commit(session.session_id, cleanDecision(session.proposal)); setCommitId(result.decision_id); });
  }

  function secondRead() {
    if (!session) return;
    run("recheck", async () => setRecheck(await api.recheck(session.session_id)));
  }

  function newSession() {
    if (!session) return;
    run("fresh", async () => setFresh(await api.freshSession(symbol, session.session_id)));
  }

  function runEvidenceDelta() {
    run("delta", async () => setDelta(await api.evidenceDelta(symbol)));
  }

  function wipe() {
    run("wipe", async () => { const result = await api.wipe(symbol); setHistorical(result.constraints); setFresh(null); setRecheck(null); });
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand"><div className="brand-mark">S</div><div><div className="brand-name">SCARBOOK</div><div className="brand-subtitle">Evidence-bound decisions for autonomous agents</div></div></div>
        <div className={`mode-badge ${health.fixtures ? "fixture" : health.live ? "live" : "offline"}`}><CircleDot size={13} fill="currentColor" />{health.fixtures ? "FIXTURE MODE · NOT LIVE" : health.live ? "LIVE RYO" : "RYO NOT CONFIGURED"}</div>
      </header>

      <main>
        <section className="intro-row">
          <div><p className="kicker">DECISION EXPERIMENT / 01</p><h1>What changed what<br /><em>the agent can do next?</em></h1></div>
          <div className="intro-copy"><p>Scarbook binds a practice decision to the evidence behind it. When fresh evidence contradicts that commitment, the action space changes.</p><div className="legend"><span><i className="dot live-dot" />Evidence</span><ArrowRight size={15} /><span><i className="dot amber-dot" />Constraint</span><ArrowRight size={15} /><span><i className="dot dark-dot" />Replan</span></div></div>
        </section>

        <section className="control-bar">
          <div className="symbol-control"><label htmlFor="symbol">ASSET</label><input id="symbol" value={symbol} onChange={(event) => setSymbol(event.target.value.toUpperCase())} maxLength={20} /></div>
          <div className="runtime-state"><span className="state-dot" />{statusText}<span className="state-line" /><span className="session-label">{session?.session_id || "NO SESSION"}</span></div>
          <button className="primary-button" onClick={start} disabled={Boolean(loading)}>{loading === "start" ? "READING RYO…" : "START SESSION"}<ArrowRight size={16} /></button>
        </section>

        {error && <div className="error-banner"><CircleAlert size={17} />{error}<button onClick={() => setError(null)}><X size={15} /></button></div>}

        <div className="step-strip"><div className={hasT0 ? "done" : "current"}><span>01</span> T0 EVIDENCE</div><ArrowRight size={14} /><div className={hasT1 ? "done" : hasCommit ? "current" : ""}><span>02</span> CONTRADICTION</div><ArrowRight size={14} /><div className={hasFresh ? "done" : hasT1 ? "current" : ""}><span>03</span> FRESH SESSION</div><ArrowRight size={14} /><div className={hasFresh ? "current" : ""}><span>04</span> ACTION GATE</div></div>

        <div className="experiment-grid">
          <section className="panel panel-t0">
            <div className="panel-header"><div><span className="panel-number">01 / T0</span><h2>Initial evidence + commitment</h2></div><span className="panel-status">{session ? "OBSERVED" : "WAITING"}</span></div>
            {!session ? <div className="empty-panel"><Sparkles size={25} /><p>Start a session to receive<br />the first live evidence receipt.</p></div> : <>
              <div className="session-chip"><GitBranch size={14} />{session.session_id}<span>FRESH SESSION</span></div>
              <Evidence receipt={session.receipt} title="LIVE EVIDENCE RECEIPT" />
              <DecisionCard decision={session.proposal} label="AGENT PROPOSAL" />
              {!hasCommit ? <button className="wide-button dark" onClick={commit} disabled={Boolean(loading)}>{loading === "commit" ? "COMMITTING…" : "COMMIT DECISION"}<LockKeyhole size={15} /></button> : <div className="confirmed"><Check size={15} />DECISION COMMITTED · {commitId}</div>}
            </>}
          </section>

          <section className="panel panel-contradiction">
            <div className="panel-header"><div><span className="panel-number">02 / T1</span><h2>Evidence changes</h2></div><span className="panel-status amber-text">{hasT1 ? (recheck?.contradiction ? "DETECTED" : "CLEAR") : "WAITING"}</span></div>
            {!hasCommit ? <div className="empty-panel"><ShieldCheck size={25} /><p>Commit the decision, then<br />request a second live read.</p></div> : !hasT1 ? <div className="action-prompt"><p>Fetch a second RYO observation. T1 is always a new request; the original receipt will never be reused.</p><button className="wide-button amber" onClick={secondRead} disabled={Boolean(loading)}>{loading === "recheck" ? "READING AGAIN…" : "SECOND LIVE READ"}<RotateCcw size={15} /></button></div> : <>
              <div className="comparison"><div><span>VERDICT</span><b>{upper(session?.receipt.evidence.data.verdict)}</b></div><ArrowRight size={17} /><div><span>NEW READ</span><b className="amber-text">{upper(currentRecheck.t1.evidence.data.verdict)}</b></div></div>
              <div className="comparison"><div><span>RISK</span><b>{upper(session?.receipt.evidence.data.risk)}</b></div><ArrowRight size={17} /><div><span>NEW READ</span><b className="amber-text">{upper(currentRecheck.t1.evidence.data.risk)}</b></div></div>
              <div className="read-pair"><span>T0 {formatTime(currentRecheck.t0.as_of)} · {currentRecheck.t0.hash_short}</span><span>T1 {formatTime(currentRecheck.t1.as_of)} · {currentRecheck.t1.hash_short}</span></div>
              {currentRecheck.constraint ? <ConstraintCard constraint={currentRecheck.constraint} /> : <div className="no-contradiction"><Check size={18} />No material contradiction detected.</div>}
            </>}
          </section>

          <section className="panel panel-fresh">
            <div className="panel-header"><div><span className="panel-number">03 / T2</span><h2>Fresh agent session</h2></div><span className="panel-status">{hasFresh ? (currentFresh.replanned ? "REPLANNED" : "FINALIZED") : "WAITING"}</span></div>
            {!hasT1 ? <div className="empty-panel"><GitBranch size={25} /><p>The next agent receives a new<br />session, evidence, and constraints.</p></div> : !hasFresh ? <div className="action-prompt"><div className="constraint-count">{activeConstraints.length} active evidence-bound constraint{activeConstraints.length === 1 ? "" : "s"}</div><p>Conversation history does not cross this boundary. The runtime carries only enforceable constraints.</p><button className="wide-button dark" onClick={newSession} disabled={Boolean(loading)}>{loading === "fresh" ? "STARTING FRESH SESSION…" : "START FRESH SESSION"}<ArrowRight size={15} /></button></div> : <>
              <div className="session-chip"><GitBranch size={14} />{currentFresh.session_id}<span>PARENT {session?.session_id}</span></div>
              <DecisionCard decision={currentFresh.proposal} label="FRESH AGENT PROPOSAL" muted />
              <div className={`gate-result ${currentFresh.gate.allowed ? "allowed" : "blocked"}`}><div className="gate-heading"><span>ACTION GATE</span>{currentFresh.gate.allowed ? <Check size={17} /> : <X size={17} />}</div><strong>{currentFresh.gate.allowed ? "ALLOWED" : "REJECTED"}</strong>{currentFresh.gate.reason && <p>{currentFresh.gate.reason.replaceAll("_", " ")} · {currentFresh.gate.constraint_ids.join(", ")}</p>}</div>
              {currentFresh.replanned ? <div className="replan-arrow"><ArrowRight size={15} /> REPLANNING <ArrowRight size={15} /></div> : <div className="replan-arrow accepted-line"><Check size={15} /> NO REPLAN NEEDED</div>}
              <DecisionCard decision={currentFresh.final_decision} label="FINAL PRACTICE DECISION" />
            </>}
          </section>
        </div>

        <section className="bottom-row"><div className="quote-block"><span className="quote-mark">“</span><p>Memory tells an agent what happened.<br /><strong>Scarbook changes what it can do next.</strong></p></div><div className="constraint-history"><div className="history-heading"><span>CONSTRAINT LEDGER</span><button onClick={wipe} disabled={Boolean(loading) || !activeConstraints.length}>{loading === "wipe" ? "WIPING…" : "WIPE ACTIVE"}</button></div>{(historical.length ? historical : activeConstraints).length ? <div className="ledger-list">{(historical.length ? historical : activeConstraints).map((constraint) => <ConstraintCard key={constraint.id} constraint={constraint} />)}</div> : <div className="ledger-empty">No evidence-bound constraints yet. The historical record will remain after a wipe.</div>}</div></section>
        <section className="skill-panel">
          <div className="skill-header">
            <div><span className="panel-number">TRACK 03 / NEW SKILL</span><h2>Evidence delta</h2><p>Compare two sequential RYO observations and report what changed—without guessing when evidence is missing.</p></div>
            <button className="wide-button amber" onClick={runEvidenceDelta} disabled={Boolean(loading)}>{loading === "delta" ? "COMPARING RYO…" : "RUN EVIDENCE DELTA"}<Sparkles size={15} /></button>
          </div>
          <EvidenceDeltaCard delta={delta} />
        </section>
      </main>
      <footer><span>SCARBOOK / PRACTICE-TRADING RESEARCH PROTOTYPE</span><span>AGENT PROPOSES · RUNTIME ENFORCES</span></footer>
    </div>
  );
}
