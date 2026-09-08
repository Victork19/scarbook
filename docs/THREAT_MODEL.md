# Threat model

## Secret boundary

`RYO_MCP_KEY` exists only in the backend environment. Do not prefix it with `VITE_` or `NEXT_PUBLIC_`, and do not put it in browser requests. CORS is an explicit origin list.

## Evidence integrity

- Missing evidence fields remain null.
- A receipt's canonical evidence hash covers only decision-relevant fields.
- T1 is a new adapter request and is stored as a distinct receipt.
- A constraint references a source decision and trigger receipt.
- Duplicate T1 calls for a session are idempotent.

## Runtime enforcement

Constraint status, priority, and gate decisions are deterministic. The LLM only proposes and replans. A final action is returned only after it passes the gate; replanning is bounded.

## Deployment

Run Uvicorn on loopback behind Nginx/HTTPS. Store SQLite and raw evidence under a private data directory. Configure Cloudflare to bypass cache for `/api/*` and `/health`; a cached T1 would invalidate the experiment.

