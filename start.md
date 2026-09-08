# Scarbook

## Evidence-Bound Decision Constraints for Autonomous Agents

**Hackathon:** RYO-CHAN Hackathon 2026
**Primary track:** Track 1 — Autonomous Agents
**Secondary opportunity:** Track 2 — Dashboards & Interfaces
**Submission deadline:** September 8, 2026, 23:59 JST. RYO's public page states that Track 1 rewards agents that interpret market evidence and record practice trades, with strong entries showing cause/effect and repeatable reasoning trails.

---

# 1. Executive Specification

Scarbook is a runtime decision layer placed between an autonomous agent and its future actions.

The system does not attempt to replace RYO-CHAN's market intelligence. RYO already supplies live research tools including `market_overview`, `scan_market`, `analyze_token`, `deep_analysis`, `compare_tokens`, `check_safety`, and `supported_tokens`. The platform describes these tools as read-only and emphasizes live data and honest provenance.

Scarbook adds a missing behavioral layer:

```text
LIVE EVIDENCE
      ↓
AGENT INTERPRETATION
      ↓
PRACTICE DECISION
      ↓
COMMITMENT + EVIDENCE HASH
      ↓
FRESH LIVE EVIDENCE
      ↓
CONTRADICTION DETECTION
      ↓
EVIDENCE-BOUND CONSTRAINT
      ↓
FRESH AGENT SESSION
      ↓
ACTION GATE
      ↓
ALLOW / REDUCE / REJECT
      ↓
REPLAN
```

The defining principle is:

> **Memory records what happened. Scarbook changes what the agent can do next.**

---

# 2. The Actual Problem

Modern agent systems can persist information across sessions. Long-term agent memory is already a standard pattern in current frameworks; LangGraph, for example, supports persistent memory across conversations and sessions. Reflexion demonstrated learning from prior feedback through episodic textual memory.

That creates a weakness:

An agent can remember:

```text
"I previously went LONG on SOL."
```

but the future agent can still decide:

```text
"I'm going LONG on SOL again."
```

unless the system turns past experience into something that actually constrains behavior.

Scarbook therefore separates:

```text
memory
```

from:

```text
behavioral constraint
```

The question Scarbook answers is:

> When new evidence materially contradicts an evidence-backed decision, how does that contradiction become enforceable behavior for a future agent?

---

# 3. Novelty Positioning

## 3.1 What Scarbook must NOT claim

Do not claim:

> “Scarbook invents scars for AI agents.”

A July 13, 2026 paper by Tengjiao Liu already describes “Scars” as compact, signed runtime constraint patches that are cached and inherited by future agent cohorts. The paper explicitly frames them as persistent runtime constraints derived from failures.

Do not claim:

> “Scarbook is the first system that lets agents learn from failure.”

Reflexion is earlier work on improving future agent decisions from feedback stored in episodic memory.

Do not claim:

> “Scarbook introduces runtime action gating.”

Runtime policy/action enforcement is already an active research area; AgentSpec and newer work address customizable runtime enforcement and action-level controls.

## 3.2 What Scarbook actually contributes

Scarbook's specific contribution is the composition of four mechanisms:

```text
1. Evidence-backed decision commitment
2. Cross-read contradiction detection
3. Evidence-bound constraint compilation
4. Fresh-session action gating + re-planning
```

The novelty claim should be about the **workflow and mechanism in the RYO context**, not about inventing persistent constraints generally.

Formalize the primitive as:

> **Evidence-Bound Constraint (EBC)**

The UI can continue calling it a:

> **Scar**

because that is memorable branding.

Internally:

```text
Scar = EvidenceBoundConstraint
```

---

# 4. Product Definition

## 4.1 Core user experience

The user selects a token:

```text
SOL
```

Scarbook launches Session 1.

The agent calls RYO and receives live evidence.

It reasons:

```text
VERDICT: bullish
RISK: low
RSI14: 64

THESIS:
Momentum and risk profile support a bullish practice trade.

DECISION:
LONG

SIZE:
1.0
```

The user clicks:

```text
COMMIT
```

Scarbook stores the complete decision provenance.

Then the system obtains another live RYO read.

Suppose:

```text
VERDICT: bearish
RISK: high
RSI14: 39
```

Scarbook compares the evidence.

It detects:

```text
bullish → bearish
low → high
```

and therefore creates:

```text
SC-001

Constraint:
LONG BLOCKED

Reason:
Committed thesis contradicted by later live evidence.
```

A completely new session starts.

The new agent does not inherit the previous conversation.

It receives:

```text
fresh evidence
+
active evidence-bound constraints
```

It proposes:

```text
LONG
```

The action gate rejects it:

```text
BLOCKED

SC-001 prohibits LONG.

REPLAN REQUIRED.
```

The agent changes its plan:

```text
NO NEW POSITION
```

That is the entire product story.

---

# 5. Winning Principle

Do not optimize for feature count.

Optimize for one undeniable causal chain:

```text
I believed X
because evidence Y

then evidence changed to Z

therefore X became invalid

Scarbook created constraint C

a new agent attempted X

Scarbook prevented X

the agent replanned
```

A judge should understand the system in less than 30 seconds.

This is especially aligned with the official Track 1 language around cause/effect and repeatable reasoning trails.

---

# 6. System Architecture

Use this architecture:

```text
                         ┌─────────────────────────┐
                         │       RYO-CHAN          │
                         │                         │
                         │  LIVE RESEARCH TOOLS    │
                         │                         │
                         │ analyze_token           │
                         │ check_safety (optional) │
                         │ etc.                    │
                         └────────────┬────────────┘
                                      │
                                      │ live evidence
                                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                         SCARBOOK API                             │
│                         FastAPI / EC2                            │
│                                                                 │
│  ┌────────────────┐     ┌──────────────────┐                   │
│  │ RYO Adapter    │────▶│ Evidence         │                   │
│  │                │     │ Normalizer       │                   │
│  └────────────────┘     └────────┬─────────┘                   │
│                                  │                              │
│                                  ▼                              │
│                        ┌──────────────────┐                     │
│                        │ Canonical Hash    │                     │
│                        └────────┬─────────┘                     │
│                                 │                              │
│                                 ▼                              │
│                        ┌──────────────────┐                     │
│                        │ Agent Reasoner    │                     │
│                        └────────┬─────────┘                     │
│                                 │                              │
│                          decision/commit                       │
│                                 │                              │
│                                 ▼                              │
│                        ┌──────────────────┐                     │
│                        │ Decision Ledger   │                     │
│                        └────────┬─────────┘                     │
│                                 │                              │
│                         T1 fresh evidence                      │
│                                 │                              │
│                                 ▼                              │
│                        ┌──────────────────┐                     │
│                        │ Contradiction    │                     │
│                        │ Engine            │                     │
│                        └────────┬─────────┘                     │
│                                 │                              │
│                                 ▼                              │
│                        ┌──────────────────┐                     │
│                        │ Constraint       │                     │
│                        │ Compiler         │                     │
│                        └────────┬─────────┘                     │
│                                 │                              │
│                                 ▼                              │
│                        ┌──────────────────┐                     │
│                        │ Action Gate      │                     │
│                        └────────┬─────────┘                     │
│                                 │                              │
│                         ALLOW / REJECT                        │
│                                 │                              │
│                          REPLAN LOOP                           │
│                                                                 │
│                    SQLite + raw evidence                        │
└─────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
                         ┌──────────────────────┐
                         │ React / Vite         │
                         │ Cloudflare Pages     │
                         └──────────────────────┘
```

---

# 7. Deployment Architecture

## Frontend

```text
React
Vite
Cloudflare Pages
```

Production:

```text
https://scarbook.YOURDOMAIN
```

## Backend

```text
Ubuntu EC2
FastAPI
Uvicorn
Nginx
SQLite
```

Production:

```text
https://api.YOURDOMAIN
```

## External dependency

Only the backend talks to RYO.

```text
Browser
  ✕ RYO

Browser
  ↓
Scarbook API
  ↓
RYO
```

Never expose:

```text
RYO_MCP_KEY
```

to the browser.

---

# 8. Repository Structure

Use:

```text
scarbook/
│
├── README.md
├── .env.example
├── .gitignore
│
├── apps/
│   │
│   ├── api/
│   │   ├── requirements.txt
│   │   │
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py
│   │   │   ├── config.py
│   │   │   ├── schemas.py
│   │   │   ├── ryo.py
│   │   │   ├── normalize.py
│   │   │   ├── hashing.py
│   │   │   ├── agent.py
│   │   │   ├── contradiction.py
│   │   │   ├── constraints.py
│   │   │   ├── gate.py
│   │   │   ├── resolver.py
│   │   │   ├── db.py
│   │   │   ├── models.py
│   │   │   └── utils.py
│   │   │
│   │   ├── fixtures/
│   │   │   ├── bullish.json
│   │   │   ├── bearish.json
│   │   │   └── unavailable.json
│   │   │
│   │   └── tests/
│   │       ├── test_normalize.py
│   │       ├── test_hash.py
│   │       ├── test_contradiction.py
│   │       ├── test_constraints.py
│   │       ├── test_gate.py
│   │       └── test_api.py
│   │
│   └── web/
│       ├── package.json
│       ├── vite.config.ts
│       └── src/
│           ├── main.tsx
│           ├── App.tsx
│           ├── api.ts
│           ├── types.ts
│           └── App.css
│
├── deploy/
│   ├── scarbook.service
│   ├── nginx-scarbook.conf
│   └── cloudflare.md
│
├── docs/
│   ├── ARCHITECTURE.md
│   ├── DEMO_SCRIPT.md
│   ├── THREAT_MODEL.md
│   └── PRIOR_WORK.md
│
└── submissions/
    └── PROJECT_SUBMISSION.pdf
```

---

# 9. Environment Configuration

## Backend

```env
RYO_MCP_URL=https://app-ryochan.com/api/mcp
RYO_MCP_KEY=

SCARBOOK_FIXTURES=0

DATABASE_PATH=/var/lib/scarbook/scarbook.db
RAW_DIR=/var/lib/scarbook/raw

CORS_ORIGINS=http://localhost:5173,https://scarbook.pages.dev,https://scarbook.YOURDOMAIN

# Groq OpenAI-compatible API
LLM_PROVIDER=https://api.groq.com/openai/v1
LLM_API_KEY=
LLM_MODEL=openai/gpt-oss-20b
```

The exact RYO request contract must be verified against the event's current builder documentation before locking implementation. The official public site confirms that RYO tools are available over MCP and REST, but does not expose all request-body details on the landing page.

---

# 10. RYO Adapter

## Responsibility

`ryo.py` is the only module permitted to know how to communicate with RYO.

It should expose a stable internal function:

```python
async def call_ryo(
    tool: str,
    payload: dict,
) -> RyoResponse:
    ...
```

The rest of the code should not care whether RYO was accessed through MCP, REST, or fixtures.

---

# 11. RYO Reliability Rules

RYO explicitly emphasizes honest provenance: if dependencies fail, the response should say so rather than pretending data exists. Scarbook should preserve that property.

Therefore:

```text
live
fixture
unavailable
error
```

must never be conflated.

Never do:

```python
rsi = payload.get("rsi14", 0)
```

Do:

```python
rsi = payload.get("rsi14")
```

Never turn:

```text
null
```

into:

```text
0
```

because zero is a meaningful number.

---

# 12. Fixture Policy

Fixtures are strictly for development and failure testing.

Environment:

```env
SCARBOOK_FIXTURES=1
```

must produce a visible frontend banner:

```text
FIXTURE MODE
NOT LIVE RYO DATA
```

When:

```env
SCARBOOK_FIXTURES=0
```

the banner becomes:

```text
LIVE RYO
```

The organizer must never see a simulated result represented as real.

Your existing rule to ensure the fixture state matches the `/health` banner is correct.

---

# 13. Normalized Evidence Envelope

Every RYO result becomes a normalized envelope:

```json
{
  "schema_version": "1.0",
  "tool": "analyze_token",
  "status": "ok",
  "data_mode": "live",
  "as_of": "2026-09-08T10:44:17Z",
  "request": {
    "symbol": "SOL"
  },
  "data": {
    "verdict": "bullish",
    "risk": "low",
    "rsi14": 64.2
  },
  "warnings": []
}
```

Display-only summaries should not participate in the decision hash.

---

# 14. Canonical Evidence

Hash only fields that matter to the decision.

For MVP:

```text
symbol
tool
schema_version
status
data_mode
as_of
verdict
risk
rsi14
```

Canonicalization:

```python
canonical = json.dumps(
    evidence,
    sort_keys=True,
    separators=(",", ":"),
    ensure_ascii=False,
)
```

Hash:

```python
hashlib.sha256(
    canonical.encode("utf-8")
).hexdigest()
```

Store:

```text
full hash
```

Display:

```text
first 8 characters
```

Example:

```text
84F2A91C...
```

---

# 15. Why Hashing Matters

The hash is not there to make the demo look “crypto.”

It establishes:

> This exact evidence is the evidence from which the decision was made.

A scar should therefore reference:

```text
T0 evidence hash
T1 evidence hash
```

rather than merely:

```text
"RYO changed its mind"
```

This gives every decision a provenance chain.

---

# 16. Data Model

Do not overcomplicate the database.

SQLite is sufficient for the event.

## sessions

```text
id
created_at
parent_session_id nullable
status
```

Example:

```text
session_001
session_002
```

`parent_session_id` allows you to show that Session 2 is a new session derived from the same environment but not the same conversation.

---

## evidence_receipts

```text
id
session_id
symbol
phase
tool
as_of
status
data_mode
evidence_json
evidence_hash
raw_path
created_at
```

Phase:

```text
t0
t1
t2
```

These labels are useful for the demo.

---

## decisions

Add a dedicated table instead of burying everything inside receipts.

```text
id
session_id
receipt_id
symbol
side
size
thesis
confidence
created_at
```

Example:

```text
DEC-001
SOL
LONG
1.0
"Momentum and low risk support a bullish position."
```

---

## constraints

```text
id
symbol
source_decision_id
trigger_receipt_id
class
constraint
parameter
blocked_side
max_size
reason
citation
active
created_at
```

Recommended classes:

```text
thesis
risk
data
```

Recommended constraints:

```text
side_blocked
size_cap
no_new_position
```

---

# 17. Stronger Constraint Representation

Don't only store:

```text
constraint = "side_blocked"
```

Store the resulting action policy.

Example:

```json
{
  "constraint": "side_blocked",
  "action_policy": {
    "LONG": "DENY",
    "SHORT": "ALLOW",
    "NONE": "ALLOW"
  }
}
```

For a size constraint:

```json
{
  "constraint": "size_cap",
  "action_policy": {
    "LONG": {
      "max_size": 0.25
    }
  }
}
```

This makes the gate generic.

---

# 18. Agent Architecture

The agent should be real.

Do not fake agentic behavior with a hardcoded sentence.

However, do not build a giant LangGraph/AutoGen system either.

You can implement the entire agent as a small state machine around one LLM.

Current agent frameworks already provide persistent memory and orchestration, but pulling in a heavy framework this late would increase failure surface without helping your demo.

Use:

```text
FastAPI
+
Pydantic
+
one LLM
+
your own loop
```

---

# 19. Agent Output Schema

Force structured output.

Conceptually:

```python
class AgentDecision(BaseModel):
    thesis: str
    side: Literal["long", "short", "none"]
    size: Literal[0.0, 0.25, 1.0]
    confidence: float
    evidence_used: list[str]
```

The model should never directly execute a trade.

It only proposes:

```text
action
```

Scarbook decides:

```text
whether action is permitted
```

That separation is critical.

---

# 20. Agent Prompt

The system prompt should establish:

```text
You are the Scarbook practice-trading agent.

You receive current RYO evidence.

You must produce:
1. a concise thesis,
2. a side,
3. a position size,
4. confidence,
5. evidence identifiers.

You must distinguish evidence from inference.

You must never claim unavailable data is available.

You are proposing a practice trade only.

You are not executing a real trade.
```

For later sessions:

```text
ACTIVE EVIDENCE-BOUND CONSTRAINTS

You must treat these as runtime action restrictions.

Do not merely mention them.

Before finalizing an action, verify that the proposed action satisfies every active constraint.

If your preferred action is blocked:
1. state the blocked action,
2. identify the constraint,
3. select a permitted alternative,
4. provide the revised practice decision.
```

---

# 21. Agent Loop

The loop should look like:

```python
evidence = get_current_evidence(symbol)

decision = agent.decide(evidence)

if session_has_active_constraints:
    gate_result = gate.check(decision)

    if gate_result.allowed:
        return decision

    replanned = agent.replan(
        evidence=evidence,
        blocked_decision=decision,
        gate_result=gate_result,
    )

    return gate.verify(replanned)
```

Maximum loop:

```text
3 iterations
```

Never allow infinite re-planning.

---

# 22. Commitment Concept

This is a key part of the invention.

A decision is not automatically a commitment merely because the LLM generated it.

It becomes committed only when:

```text
evidence was live
+
decision was structured
+
user/system committed the practice trade
```

Then:

```text
DEC-001
```

is immutable.

That prevents the system from retroactively rewriting its history.

---

# 23. T0

T0 is the initial evidence snapshot.

Sequence:

```text
POST /api/session/start
        ↓
call RYO
        ↓
normalize
        ↓
hash
        ↓
agent analyzes
        ↓
agent proposes practice trade
        ↓
user clicks COMMIT
        ↓
decision saved
```

Response:

```json
{
  "session_id": "sess_001",
  "receipt_id": "rcpt_001",
  "decision_id": "dec_001",
  "evidence": {
    "symbol": "SOL",
    "verdict": "bullish",
    "risk": "low",
    "rsi14": 64.2,
    "as_of": "..."
  },
  "decision": {
    "side": "long",
    "size": 1.0,
    "thesis": "..."
  },
  "evidence_hash": "84f2a91c..."
}
```

---

# 24. T1

T1 must be a new live RYO call.

Never retrieve T0 from your database and pretend it is the second read.

That would destroy the central experiment.

Sequence:

```text
T0 evidence
      +
fresh RYO call
      ↓
T1 evidence
      ↓
comparison
```

Both timestamps must be visible.

---

# 25. Contradiction Engine

Do not ask the LLM:

> “Does this contradict the previous result?”

For the core gate, use deterministic rules.

This is important because an LLM-based contradiction decision can be inconsistent.

---

# 26. Contradiction Classes

## Class A — Thesis contradiction

Example:

```text
T0 verdict = bullish
T1 verdict = bearish
```

and:

```text
T0 side = LONG
```

Generate:

```text
constraint = side_blocked
blocked_side = LONG
```

---

## Class B — Risk escalation

Example:

```text
T0 risk = low
T1 risk = high
```

while the side remains unchanged.

Generate:

```text
constraint = size_cap
max_size = 0.25
```

---

## Class C — Data failure

Example:

```text
T1.status != ok
```

or:

```text
T1.data_mode != live
```

Generate:

```text
constraint = no_new_position
```

This follows the same honesty principle RYO itself emphasizes: unavailable data must remain unavailable rather than being represented as live.

---

# 27. Do Not Create Price-Only Scars

This is correct in your original plan.

A price movement by itself should not automatically create a behavioral constraint.

Otherwise the project becomes:

```text
price changed
→ block action
```

which is not a meaningful contradiction mechanism.

The trigger should be tied to a change in the evidence interpretation:

```text
verdict
risk
data validity
```

---

# 28. Risk Ordering

Define explicitly:

```python
RISK_ORDER = {
    "low": 1,
    "medium": 2,
    "high": 3,
}
```

Then:

```python
risk_escalated = (
    RISK_ORDER[t1.risk] >
    RISK_ORDER[t0.risk]
)
```

Do not rely on string comparison.

---

# 29. Verdict Mapping

Do not guess which exact RYO strings represent bullish/bearish states.

First make one live call.

Then freeze the mapping in code and README.

Example:

```python
VERDICT_TO_SIDE = {
    "bullish": "long",
    "bearish": "short",
}
```

If RYO uses different strings, use the actual returned strings.

Document:

```text
Observed RYO verdict string
        ↓
Scarbook normalized interpretation
```

---

# 30. Priority Rules

Multiple constraints may exist simultaneously.

Use deterministic priority:

```text
NO_NEW_POSITION
        >
SIDE_BLOCKED
        >
SIZE_CAP
```

Example:

```text
SC-001 side_blocked LONG
SC-002 size_cap 0.25
SC-003 no_new_position
```

Final effective policy:

```text
all new positions blocked
```

Do not let the LLM decide which constraint wins.

---

# 31. Action Gate

The action gate is arguably the most important technical component.

Input:

```json
{
  "symbol": "SOL",
  "side": "long",
  "size": 1.0
}
```

Output:

```json
{
  "allowed": false,
  "effective_action": null,
  "reason": "side_blocked",
  "constraint_ids": [
    "SC-001"
  ],
  "citation": "RYO verdict bullish at T0 → bearish at T1..."
}
```

For a reduced position:

```json
{
  "allowed": true,
  "effective_action": {
    "side": "long",
    "size": 0.25
  },
  "modified": true,
  "constraint_ids": [
    "SC-002"
  ]
}
```

This is the point where Scarbook becomes a behavioral control system rather than a memory database.

---

# 32. New Session

A new session must genuinely be new.

Do not pass:

```text
previous chat history
```

into the new agent.

Instead pass:

```text
fresh session ID
+
current evidence
+
active constraint summary
```

This lets you prove that persistence is externalized.

The question becomes:

> Can the behavior survive the conversation dying?

That is much stronger than showing a chatbot remembering something.

---

# 33. T2

T2 sequence:

```text
new session
    ↓
fresh RYO evidence
    ↓
load active constraints
    ↓
agent proposes decision
    ↓
action gate
    ↓
if blocked → replan
    ↓
final decision
```

Response:

```json
{
  "session_id": "sess_002",
  "evidence_receipt_id": "rcpt_003",
  "decision": {
    "side": "none",
    "size": 0
  },
  "gate": {
    "original_action": {
      "side": "long",
      "size": 1.0
    },
    "allowed": false,
    "constraint": "SC-001"
  },
  "replanned": true
}
```

---

# 34. Wipe

Wipe should not delete evidence.

It should deactivate constraints.

Bad:

```sql
DELETE FROM constraints
```

Good:

```sql
UPDATE constraints
SET active = 0
WHERE symbol = ?
```

Why?

Because your audit trail should still show:

```text
SC-001 existed
SC-001 blocked LONG
SC-001 was later wiped
```

That creates a much stronger provenance story.

---

# 35. Future Constraint Resolution

Do not build this deeply tonight, but architect for it.

Current lifecycle:

```text
CREATED
  ↓
ACTIVE
  ↓
WIPED
```

Future lifecycle:

```text
CREATED
  ↓
ACTIVE
  ├── reinforced
  ├── resolved by evidence
  ├── expired
  └── manually wiped
```

This gives the project a believable path beyond the hackathon.

---

# 36. API Design

Recommended API:

```text
GET  /health

POST /api/session
POST /api/decision/commit
POST /api/recheck
POST /api/action/check
POST /api/session/new
POST /api/wipe

GET  /api/state
GET  /api/constraints/{symbol}
GET  /api/sessions/{id}
```

You can internally maintain T0/T1/T2 labels.

But the public semantics should be:

```text
session
decision
recheck
action
```

because those sound like an actual agent system rather than test fixtures.

---

# 37. `/health`

Return:

```json
{
  "live": true,
  "fixtures": false,
  "ryo_reachable": true
}
```

Frontend banner:

```text
● LIVE RYO
```

or:

```text
● FIXTURE MODE
```

Do not make the banner dependent solely on an environment variable.

It should reflect actual backend state.

---

# 38. `/api/state`

Return:

```json
{
  "symbol": "SOL",
  "session_id": "sess_002",
  "active_constraints": [
    {
      "id": "SC-001",
      "class": "thesis",
      "constraint": "side_blocked",
      "blocked_side": "long",
      "citation": "..."
    }
  ],
  "latest_decision": {
    "side": "none",
    "size": 0
  }
}
```

---

# 39. Frontend

Do not build a dashboard.

Build an **experiment**.

One screen.

Header:

```text
SCARBOOK
Evidence-bound decisions for autonomous agents
```

Top-right:

```text
● LIVE RYO
```

---

# 40. Panel 1 — T0

Show:

```text
SESSION 01

SOL

LIVE EVIDENCE
──────────────

Verdict      BULLISH
Risk         LOW
RSI14        64.2

As of        18:42:11
Hash         84F2A91C

AGENT THESIS
"Momentum and current risk support a bullish
practice position."

PROPOSED ACTION

LONG
1.0

[ COMMIT DECISION ]
```

---

# 41. Panel 2 — Contradiction

After T1:

```text
SECOND LIVE READ

VERDICT
BULLISH → BEARISH

RISK
LOW → HIGH

RSI14
64.2 → 38.7

CONTRADICTION DETECTED
```

Then:

```text
SC-001

LONG
BLOCKED

Why?

The new live RYO evidence contradicts
the committed bullish thesis.

T0
18:42:11
hash 84F2A91C

T1
18:43:07
hash 19AB27FE
```

This should be the visual centerpiece.

---

# 42. Panel 3 — New Session

Display:

```text
SESSION 02
FRESH AGENT

Active constraints: 1

Agent proposal
──────────────

LONG 1.0

ACTION GATE
───────────

✕ REJECTED

SC-001
LONG BLOCKED

REPLANNING...
```

Then animate or reveal:

```text
REVISED PRACTICE DECISION

NO NEW POSITION
```

This is the money shot.

---

# 43. Panel 4 — Wipe

Keep it tiny.

```text
ACTIVE SCARS
SC-001

[ WIPE CONSTRAINTS ]
```

After click:

```text
SC-001
INACTIVE

Action space restored.
```

Then make the next action show:

```text
LONG AVAILABLE
```

The historical record remains visible.

---

# 44. Avoid These UI Features

Do not build:

```text
portfolio analytics
P&L charts
wallet screens
price charts
leaderboards
social feeds
profiles
authentication
notifications
settings pages
```

None of them increase your winning probability for this demonstration.

RYO already owns the market-information surface.

---

# 45. Security Model

## Secret boundary

The only secret that matters:

```text
RYO_MCP_KEY
```

It exists exclusively on EC2.

Never:

```text
VITE_RYO_MCP_KEY
```

Never:

```text
NEXT_PUBLIC_RYO_KEY
```

Never put the key in frontend code.

---

# 46. EC2 Permissions

Recommended:

```text
scarbook
```

user.

Directories:

```text
/opt/scarbook
/var/lib/scarbook
```

Permissions:

```text
/opt/scarbook           750
/var/lib/scarbook       700
.env                    600
scarbook.db             600
raw/                    700
```

---

# 47. Uvicorn

Bind:

```text
127.0.0.1:8000
```

not:

```text
0.0.0.0:8000
```

Nginx handles public traffic.

---

# 48. Nginx

Flow:

```text
Internet
    ↓
HTTPS
    ↓
Nginx :443
    ↓
127.0.0.1:8000
```

Do not expose Uvicorn directly.

---

# 49. Cloudflare

Production:

```text
scarbook.YOURDOMAIN → Pages
api.YOURDOMAIN      → EC2
```

For API routes:

```text
Cache-Control: no-store
```

and Cloudflare cache bypass for:

```text
/api/*
/health
```

A cached second read is catastrophic for this project because the central claim is that T1 is live and new.

---

# 50. CORS

Explicit origins:

```python
allow_origins=[
    "https://scarbook.YOURDOMAIN",
    "https://scarbook.pages.dev",
    "http://localhost:5173",
]
```

Never:

```python
allow_origins=["*"]
```

---

# 51. Concurrency / Database Safety

SQLite is enough for the hackathon, but the critical writes must be transactional.

For commitment:

```text
BEGIN
create receipt
create decision
COMMIT
```

For scar generation:

```text
BEGIN
create constraint
mark linked contradiction processed
COMMIT
```

Use one database transaction for logically inseparable operations.

---

# 52. Idempotency

The following operations should be idempotent:

```text
commit
recheck
wipe
```

At minimum, avoid creating multiple constraints for the same T0/T1 pair.

Create a uniqueness rule such as:

```text
(unique symbol, t0_receipt_id, t1_receipt_id)
```

This protects against duplicate button clicks and network retries.

---

# 53. RYO Retry Policy

For transient failures:

```text
429
503
504
```

use:

```text
1 retry
```

with small backoff.

Do not retry everything indefinitely.

For permanent errors:

```text
400
401
403
```

return a clear error.

The user should see:

```text
RYO unavailable
No decision committed
```

rather than a fabricated decision.

That aligns with RYO's stated honesty/provenance model.

---

# 54. Evidence Integrity Invariants

These are your most important backend invariants.

### Invariant 1

A decision may not be committed unless the evidence is:

```text
status == ok
AND
data_mode == live
```

for the real demo.

### Invariant 2

A contradiction must reference two distinct evidence receipts.

### Invariant 3

A constraint must reference its source decision and contradictory evidence.

### Invariant 4

An inactive constraint must never block an action.

### Invariant 5

A blocked action must never be presented as an allowed action.

### Invariant 6

Fixture evidence must never be labeled live.

### Invariant 7

T1 must be a new RYO request.

### Invariant 8

T2 must use a new session ID.

### Invariant 9

A wipe must not delete historical evidence.

### Invariant 10

The final agent action must pass the action gate.

---

# 55. Tests

You need tests around the mechanism, not around CSS.

## Test 1

```text
T0 bullish
T1 bullish
```

Expected:

```text
NO SCAR
```

## Test 2

```text
T0 bullish
T1 bearish
```

Expected:

```text
LONG BLOCKED
```

## Test 3

```text
T0 low risk
T1 medium risk
```

Expected:

```text
SIZE <= 0.25
```

## Test 4

```text
T0 live
T1 unavailable
```

Expected:

```text
NO_NEW_POSITION
```

## Test 5

```text
active scar
new session
```

Expected:

```text
constraint remains
```

## Test 6

```text
wipe
new session
```

Expected:

```text
constraint no longer blocks
```

## Test 7

```text
duplicate T1 request
```

Expected:

```text
no duplicate scar
```

---

# 56. Golden Demo Fixture

Although the production demo must show live RYO, create a deterministic fixture suite for debugging.

Fixture sequence:

```text
T0:
verdict = bullish
risk = low
rsi14 = 64.2

T1:
verdict = bearish
risk = high
rsi14 = 38.7
```

This guarantees the full loop works before you depend on live market state.

Frontend must clearly show:

```text
FIXTURE MODE
```

during this test.

Never record the final demo with the fixture banner.

---

# 57. Live Demo Reliability Strategy

The biggest operational risk is not your code.

It is:

```text
RYO rate limit
RYO outage
market changes
LLM hallucination
network instability
```

Therefore, make your demo flow robust.

Before recording:

```text
1. Hit /health
2. Confirm live=true
3. Run one T0
4. Run one T1
5. Verify contradiction
6. Start fresh T2
7. Verify constraint gate
8. Wipe
9. Verify restoration
```

If a live contradiction does not happen naturally, do not falsify the live label.

Instead, prepare a fixture demo and explicitly label it.

But the strongest submission is a video with the full mechanism occurring from live RYO data at least once.

---

# 58. LLM Failure Handling

If the LLM returns malformed output:

```text
do not commit
```

Instead:

```text
AGENT OUTPUT INVALID
RETRYING
```

Maximum:

```text
2 retries
```

If still invalid:

```text
No decision committed.
```

Do not silently manufacture a fallback decision unless the UI says the system is using deterministic fallback mode.

---

# 59. Separate LLM Responsibilities

The LLM can:

```text
interpret evidence
write thesis
propose action
replan
```

The LLM must not be trusted to:

```text
decide whether a constraint is active
override a constraint
change evidence timestamps
change hashes
declare fixture data live
```

Those are deterministic application responsibilities.

This separation is one of the strongest technical aspects of the project.

---

# 60. Deterministic Contradiction Algorithm

Pseudo-code:

```python
def detect_contradiction(t0, t1, decision):
    if not is_trustworthy(t1):
        return Constraint(
            class_="data",
            type="no_new_position",
        )

    if (
        decision.side == "long"
        and t0.verdict in BULLISH
        and t1.verdict in BEARISH
    ):
        return Constraint(
            class_="thesis",
            type="side_blocked",
            blocked_side="long",
        )

    if (
        decision.side == "short"
        and t0.verdict in BEARISH
        and t1.verdict in BULLISH
    ):
        return Constraint(
            class_="thesis",
            type="side_blocked",
            blocked_side="short",
        )

    if risk_rank(t1.risk) > risk_rank(t0.risk):
        return Constraint(
            class_="risk",
            type="size_cap",
            max_size=0.25,
        )

    return None
```

The actual RYO verdict vocabulary must be frozen from the real payload.

---

# 61. Why the LLM Should Not Detect the Core Contradiction

Because the strongest judge question is:

> “Could the model just decide that something is a contradiction?”

Your answer becomes:

> **“No. The model interprets evidence, but the commitment and constraint rules are deterministic.”**

That is significantly stronger.

---

# 62. Agent / Gate Separation

Think of two entities:

```text
AGENT
"What do I want to do?"

GATE
"Are you allowed to do it?"
```

The agent proposes.

The Scarbook runtime enforces.

This makes the architecture legible.

---

# 63. Stronger T2 Replanning

Do not merely do:

```text
proposal blocked
```

End the process there.

Do:

```text
AGENT
    ↓
proposes LONG 1.0

GATE
    ↓
blocked

AGENT
    ↓
replans

GATE
    ↓
passes

FINAL
NO POSITION
```

This makes the system genuinely adaptive.

The constraint changes the agent's action.

---

# 64. Citation Generation

Every constraint should produce a human-readable provenance statement:

```text
RYO verdict changed from bullish at T0
to bearish at T1 between
18:42:11 and 18:43:07 UTC.

Constraint SC-001:
LONG blocked.
```

For risk:

```text
RYO risk increased from low at T0
to high at T1.

Constraint SC-002:
maximum practice size = 0.25.
```

For unavailable evidence:

```text
T1 evidence was not trustworthy because
data_mode != live or status != ok.

Constraint SC-003:
no new position.
```

---

# 65. State Machine

Formalize the entire application:

```text
IDLE
 ↓
SESSION_STARTED
 ↓
T0_OBSERVED
 ↓
DECISION_PROPOSED
 ↓
COMMITTED
 ↓
T1_OBSERVED
 ↓
CONTRADICTION_CHECKED
 ├── NO_SCAR ──────────────┐
 │                         │
 └── SCAR_CREATED          │
          ↓                │
     CONSTRAINT_ACTIVE     │
          ↓                │
       NEW_SESSION         │
          ↓                │
     ACTION_PROPOSED       │
          ↓                │
        GATED              │
      ↙       ↘            │
 BLOCKED      ALLOWED       │
    ↓            ↓          │
 REPLAN         FINAL       │
    ↓                       │
   GATE                     │
    ↓                       │
  FINAL                     │
                            │
                WIPE ←──────┘
```

This should be implemented as explicit backend state, not merely UI state.

---

# 66. Technical Terms to Use

Use:

```text
Evidence Receipt
Decision Commitment
Evidence-Bound Constraint
Constraint Gate
Action Space
Replanning
Provenance
Fresh Session
Live Evidence
```

Use “Scar” as the user-facing metaphor.

Avoid making your technical description depend on:

```text
"Scar memory"
```

because that is too close to the existing July 2026 terminology.

---

# 67. README Structure

Use:

```text
# Scarbook

## What it is
## Why it exists
## How it works
## Architecture
## RYO integration
## Evidence model
## Constraint model
## Demo
## Live vs fixture policy
## Security
## Prior work
## Limitations
## Running locally
## Deployment
```

---

# 68. Prior Work Disclosure

Put a section in the README.

Recommended wording:

> ### Prior Work
>
> Scarbook is inspired by existing research on persistent agent memory, runtime action enforcement, and failure-derived constraints. In particular, the July 2026 work “Heterogeneous Agent Cohorts for Safe Open-Ended Exploration with Runtime Constraint Memory” uses the term “Scars” for signed runtime constraint patches derived from failures and inherited by future agent cohorts. Scarbook does not claim to originate that general concept.
>
> Scarbook's implementation for this event focuses on a different application pipeline: live RYO evidence → committed practice decision → cross-read contradiction detection → evidence-bound action constraint → fresh-session action gating → agent re-planning. The system also binds each constraint to the exact RYO observations that caused it through normalized evidence and hashes.
>
> Related foundations include Reflexion-style experience-based adaptation and modern persistent-memory/runtimes for stateful agents.

That is what I meant by **disclosing** it.

You're effectively telling the judges:

> “We know the neighboring literature. Here is exactly what we are and aren't claiming.”

That is better than letting an originality reviewer discover the overlap themselves.

The official hackathon schedule says the submission period is followed by a code audit, originality check, security review and technical evaluation, so this transparency is strategically sensible.

This is not a substitute for checking the organizer's exact rules or obtaining legal advice about intellectual-property matters; it is the safest technical/originality positioning based on the publicly available information.

---

# 69. Prior Work Page in the PDF

Do not hide this.

Add one small section:

```text
RELATED WORK & DIFFERENTIATION

Persistent memory:
Agents can remember prior information.

Runtime guardrails:
Systems can constrain actions.

Scarbook:
A committed live-evidence decision is compared against
later live evidence. Only when a material contradiction is
detected is an action constraint generated, and that
constraint is enforced against a fresh agent session.
```

Diagram:

```text
MEMORY
"What happened?"

SCARBOOK
"What changed what the agent is allowed to do?"
```

That is your distinction.

---

# 70. The Most Important Architectural Differentiator

Make the chain:

```text
Evidence Receipt
      ↓
Decision Commitment
      ↓
Constraint
```

immutable.

A constraint cannot exist without provenance.

This prevents:

```text
magic database rule
```

and creates:

```text
evidence-bound behavior
```

That phrase is much stronger.

---

# 71. Why RYO Is Important

Do not let RYO look like a random API dependency.

The narrative should be:

> RYO supplies live evidence. Scarbook supplies behavioral continuity.

The official hackathon explicitly says RYO already handles market-data plumbing, while builders should create the intelligence, interface, or social mechanism that turns its research into action.

Therefore:

```text
RYO = perception
Scarbook = decision continuity
Agent = reasoning
Gate = behavioral enforcement
```

That's a coherent architecture.

---

# 72. Do Not Try to Compete With RYO

Do not build your own:

```text
technical indicator engine
market scanner
price feed
safety engine
token database
```

That wastes time and makes your entry look redundant.

RYO already has seven research tools covering those surfaces.

---

# 73. Track Strategy

## Track 1

This is your primary.

Emphasize:

```text
agent reasoning
practice trades
cause/effect
fresh sessions
replanning
constraint enforcement
```

Track 1 has the largest track prize pool at $6,000 and specifically asks for the evidence → decision trail.

## Track 2

Your UI can potentially make Scarbook competitive here too.

The Track 2 requirement is to show what changed and why it matters quickly, which your contradiction view naturally does.

But do not split the implementation into two products.

One product can demonstrate both.

---

# 74. Overall Japan Award Strategy

The public rules say the overall trip award is based on:

```text
code quality
architecture
functionality
stability
bug count
```

That means the smartest strategy is not:

> “Add more features.”

It is:

> **Make the core extremely reliable.**

That means:

```text
small architecture
clear modules
tests
honest live/fixture handling
no exposed secrets
clean deployment
reliable demo
```

---

# 75. 90-Second Demo Script

### 0:00–0:10

```text
"Scarbook makes contradictory evidence change
what an autonomous agent is allowed to do."
```

Show:

```text
● LIVE RYO
SOL
```

---

### 0:10–0:25

```text
T0

RYO → BULLISH
Risk → LOW

Agent:
LONG 1.0

COMMIT
```

---

### 0:25–0:40

Click:

```text
SECOND LIVE READ
```

Show:

```text
BULLISH → BEARISH
LOW → HIGH
```

Then:

```text
CONTRADICTION DETECTED

SC-001
LONG BLOCKED
```

---

### 0:40–0:58

Create:

```text
NEW SESSION
```

Fresh agent proposes:

```text
LONG
```

The gate interrupts:

```text
✕ BLOCKED
SC-001
```

Then:

```text
REPLANNING...
```

---

### 0:58–1:10

Show:

```text
FINAL PRACTICE DECISION

NO NEW POSITION
```

---

### 1:10–1:20

Click:

```text
WIPE
```

Show:

```text
SC-001 → INACTIVE
```

---

### 1:20–1:30

Final screen:

```text
T0
  ↓
DECISION
  ↓
CONTRADICTION
  ↓
CONSTRAINT
  ↓
NEW SESSION
  ↓
REPLANNED ACTION
```

Say:

> **“Memory tells an agent what happened. Scarbook changes what it can do next.”**

End.

---

# 76. PDF Story

The PDF should be 5–7 pages, not a giant technical manual.

### Page 1

```text
SCARBOOK

Evidence-bound decision constraints
for autonomous agents.

LIVE EVIDENCE
→
CONTRADICTION
→
CONSTRAINT
→
REPLAN
```

### Page 2

The problem.

### Page 3

Architecture.

### Page 4

T0 → T1 → T2 visual sequence.

### Page 5

Technical mechanism.

### Page 6

Why RYO + Scarbook.

### Page 7

Related work / differentiation / limitations.

---

# 77. Project Limitation Statement

Be explicit:

```text
Scarbook is a practice-trading research prototype.

It does not execute real trades.

It does not claim that an RYO contradiction is objectively
true about the market.

It demonstrates how an autonomous agent can bind a future
action to the provenance of prior evidence.
```

This keeps the claim precise.

---

# 78. What You Should Actually Implement Tonight

The minimum serious version is:

```text
1. RYO adapter
2. live evidence normalization
3. hashing
4. LLM decision
5. decision commitment
6. fresh second RYO read
7. deterministic contradiction engine
8. constraint storage
9. new session
10. action gate
11. replan
12. wipe
13. React visual flow
14. tests
15. deployment
```

Everything else is optional.

---

# 79. Kill List

Do not build:

```text
real trading
wallet integration
blockchain
NFTs
authentication
accounts
Postgres
Redis
Kubernetes
vector database
RAG
multi-agent swarm
fine-tuning
complex observability platform
social network
mobile app
price charts
billing
```

None of these materially increases the probability of winning the current event.

---

# 80. Build Order

Given the deadline, use this exact order.

## Phase 1 — Prove RYO

```text
call live RYO
↓
print normalized evidence
↓
print data_mode
↓
print as_of
```

Do not touch React yet.

---

## Phase 2 — Lock schema

Take one real payload.

Freeze:

```text
verdict path
risk path
rsi14 path
as_of path
status path
data_mode path
```

Implement normalization.

---

## Phase 3 — Build the ledger

Implement:

```text
sessions
receipts
decisions
constraints
```

Test inserts.

---

## Phase 4 — Build contradiction

Test entirely without an LLM.

```text
T0 → T1 → expected constraint
```

This must work perfectly.

---

## Phase 5 — Build action gate

Test:

```text
LONG 1.0
↓
SC-001
↓
BLOCK
```

Then:

```text
LONG 0.25
↓
SC-002
↓
ALLOW
```

---

## Phase 6 — Add agent

Agent only does:

```text
evidence → thesis → action
```

Do not give it authority to bypass the gate.

---

## Phase 7 — Replanning

Add:

```text
blocked action
↓
feedback
↓
agent replan
↓
new action
```

---

## Phase 8 — React

Only now build:

```text
T0
T1
T2
Wipe
```

The UI is a visualization of a working backend, not the reverse.

---

# 81. Definition of Done

Scarbook is submission-ready when this exact sequence works against the deployed production URL:

```text
1. Browser loads
2. LIVE RYO badge appears
3. User enters SOL
4. T0 uses live RYO
5. Agent produces LONG 1.0
6. User commits
7. T0 hash shown
8. T1 calls RYO again
9. T0 and T1 timestamps differ
10. Contradiction detected
11. SC-001 created
12. New session ID generated
13. Fresh agent proposes action
14. Gate detects SC-001
15. Proposed action blocked
16. Agent replans
17. Final action obeys SC-001
18. Wipe deactivates SC-001
19. Constraint remains visible historically
20. No RYO key appears in frontend or repository
```

If all twenty work, stop building features.

---

# 82. Final Product Definition

The cleanest possible definition of Scarbook is now:

> **Scarbook is an evidence-bound decision layer for autonomous agents. It records the evidence behind a practice decision, detects when later live evidence contradicts that decision, converts the contradiction into an enforceable action constraint, and forces fresh sessions to re-plan around the constraint.**

And the shortest pitch is:

> **An agent can remember a mistake and still repeat it. Scarbook turns contradictory evidence into a rule the next decision must obey.**

And the strongest technical sentence is:

> **Scarbook separates reasoning from enforcement: the agent proposes what it wants to do; the evidence-bound constraint layer determines what it is allowed to do.**

That is the version I would submit.
