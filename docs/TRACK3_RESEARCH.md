# Track 3 research and implementation note

Updated: 2026-09-08

## Finding

The official public RYO-CHAN hackathon page describes Track 3 as building a research tool RYO does not already have, following the published tool specification, with a Python skill contract and honesty convention. The same page lists RYO's existing read-only research surface as `market_overview`, `scan_market`, `analyze_token`, `deep_analysis`, `compare_tokens`, `check_safety`, and `supported_tokens`.

## New capability

Scarbook adds `evidence_delta`, a read-only temporal comparison tool. It calls `analyze_token` twice for one symbol and reports what changed between observations. Temporal comparison is distinct from RYO's existing token, market, safety, and cross-token research calls.

## Honesty and provenance

- Missing values remain `null` and are listed in `data.missing_fields`.
- Missing fields return `partial`; source failure returns `partial` or `unavailable`, never a fabricated successful result.
- The result preserves both observation timestamps, canonical evidence hashes, statuses, modes, warnings, and normalized before/after values.
- The tool is read-only and makes no trade recommendation.

## Contract boundary

The public hackathon page confirms the Track 3 requirement and the existing tool names, but the machine-readable published submission schema was not publicly retrievable during this implementation. `skills/evidence-delta/skill.json` therefore defines the implementation's explicit contract and the API also exposes standard JSON-RPC `tools/list` and `tools/call` methods. The submission should be checked against any organizer-provided schema before final upload.

## Source

- [RYO-CHAN Hackathon 2026](https://ryobuild.com/): Track 3 criteria, existing seven tools, read-only surface, and honesty/provenance statements; accessed 2026-09-08.
