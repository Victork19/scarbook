# Scarbook

## What it is

Scarbook is an evidence-bound decision layer for autonomous agents. It records the evidence behind a practice decision, checks a fresh RYO observation for a material contradiction, compiles that contradiction into an enforceable constraint, and makes a fresh agent session re-plan around it.

> An agent can remember a mistake and still repeat it. Scarbook turns contradictory evidence into a rule the next decision must obey.

This is a practice-trading research prototype. It never executes real trades.

## How it works

```text
T0 live evidence → agent proposal → commitment + evidence hash
       ↓
T1 fresh live evidence → deterministic contradiction engine
       ↓
evidence-bound constraint → fresh session → action gate → replan
```

The agent proposes an action. The runtime decides whether that action is allowed.

## Architecture

- `apps/api/app/ryo.py` is the only RYO integration boundary.
- `normalize.py` produces one honest evidence envelope for live, fixture, unavailable, and error results.
- `hashing.py` creates a canonical SHA-256 hash from decision-relevant evidence.
- SQLite stores immutable receipts, commitments, and a historical constraint ledger.
- `contradiction.py`, `constraints.py`, and `gate.py` are deterministic; the LLM cannot activate, bypass, or rewrite constraints.
- `apps/web` is a one-screen React/Vite experiment, not a general market dashboard.

## RYO integration

The backend calls `POST RYO_MCP_URL` with an MCP-compatible body:

```json
{"tool":"analyze_token","arguments":{"symbol":"SOL"}}
```

The adapter is intentionally isolated because the event's exact request contract may change. Update `ryo.py` when the current RYO builder documentation is available. `RYO_MCP_KEY` is backend-only and is never included in Vite environment variables or browser code.

## Evidence model

Every receipt contains `schema_version`, `tool`, `status`, `data_mode`, `as_of`, request symbol, normalized `verdict`, `risk`, `rsi14`, warnings, and a full evidence hash. The UI displays the first eight hash characters for legibility. Missing values remain missing; they are never replaced with zero.

Fixture mode is explicit: set `SCARBOOK_FIXTURES=1` and the UI shows `FIXTURE MODE · NOT LIVE`. Fixtures are never labeled live.

## Constraint model

The current deterministic rules are:

- bullish → bearish while long: `side_blocked`, long denied;
- bearish → bullish while short: `side_blocked`, short denied;
- risk escalation: `size_cap`, maximum size `0.25`;
- unavailable or non-trustworthy T1: `no_new_position`.

Priority is `no_new_position > side_blocked > size_cap`. Wipe deactivates constraints without deleting receipts, decisions, or historical constraint records.

## Demo

1. Start the API and web app.
2. Use fixture mode for a deterministic local run.
3. Start a SOL session, commit the proposal, and request a second read.
4. Start a fresh session. The first proposal is gated, then the agent replans to `NO NEW POSITION`.
5. Wipe active constraints and confirm that the ledger still shows the inactive historical record.

See [docs/DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md) for the 90-second presentation flow.

## Running locally

Backend (PowerShell):

```powershell
cd apps/api
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:SCARBOOK_FIXTURES="1"
$env:DATABASE_PATH="$pwd\data\scarbook.db"
uvicorn app.main:app --reload --port 8000
```

Frontend:

```powershell
cd apps/web
npm.cmd install
npm.cmd run dev
```

Open `http://localhost:5173`. For live mode, set `SCARBOOK_FIXTURES=0` and provide `RYO_MCP_KEY`.

### Optional Groq agent

The agent defaults to Groq's OpenAI-compatible API and uses `openai/gpt-oss-20b`, which supports JSON output. Copy `.env.example` to `.env`, then set `LLM_API_KEY` to a Groq API key (or set `GROQ_API_KEY`). The deterministic agent remains the automatic fallback if the key is missing, the model rejects a response, or Groq is temporarily unavailable.

```text
LLM_PROVIDER=https://api.groq.com/openai/v1
LLM_MODEL=openai/gpt-oss-20b
LLM_API_KEY=your-groq-key
```

Never put either LLM key in frontend variables or a submission archive.

## API

| Method | Route | Purpose |
|---|---|---|
| GET | `/health` | live/fixture and dependency status |
| POST | `/api/session` | fresh T0 session and proposal |
| POST | `/api/decision/commit` | immutable decision commitment |
| POST | `/api/recheck` | fresh T1 observation and contradiction check |
| POST | `/api/session/new` | fresh T2 session, gate, and bounded replan |
| POST | `/api/action/check` | deterministic action gate |
| POST | `/api/wipe` | deactivate constraints without deleting history |
| GET | `/api/state` | current experiment state |

## Security and deployment

The frontend deploys to Cloudflare Pages; the backend deploys as a Docker Compose service on EC2. Docker binds the API to `127.0.0.1:8000`, Nginx terminates HTTPS, and the named `scarbook-data` volume preserves SQLite and raw evidence across image rebuilds. The frontend talks only to Scarbook, never directly to RYO.

One-time EC2 bootstrap:

```bash
cd /opt/scarbook
sudo API_DOMAIN=api.example.com CERTBOT_EMAIL=ops@example.com bash ./deploy/install-ec2.sh
```

Put the production `RYO_MCP_KEY` and CORS origins in `/opt/scarbook/.env`, then deploy updates with:

```bash
sudo bash ./deploy/deploy-ec2.sh
```

Cloudflare Pages uses root `apps/web`, build command `npm run build`, output `dist`, and `VITE_API_URL=https://api.example.com`. Full details are in [deploy/cloudflare.md](deploy/cloudflare.md).

## Prior Work

Scarbook is inspired by existing research on persistent agent memory, runtime action enforcement, and failure-derived constraints. In particular, the July 2026 work “Heterogeneous Agent Cohorts for Safe Open-Ended Exploration with Runtime Constraint Memory” uses the term “Scars” for signed runtime constraint patches derived from failures and inherited by future agent cohorts. Scarbook does not claim to originate that general concept.

Scarbook's implementation for this event focuses on a different application pipeline: live RYO evidence → committed practice decision → cross-read contradiction detection → evidence-bound action constraint → fresh-session action gating → agent re-planning. Each constraint is bound to the exact RYO observations that caused it through normalized evidence and hashes.

Related foundations include Reflexion-style experience-based adaptation and modern persistent-memory/runtimes for stateful agents.

## Limitations

Scarbook does not claim that an RYO contradiction is objectively true about the market. It demonstrates how an autonomous agent can bind a future action to the provenance of prior evidence. The exact live RYO payload vocabulary and endpoint contract must be confirmed against current event documentation before production deployment. The public hackathon page confirms MCP/REST access but does not document the complete wire payload.
# scarbook
