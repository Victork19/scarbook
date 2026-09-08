# Track 3 research source report

Date: 2026-09-08

## Scope

Verify the public RYO-CHAN Track 3 requirement and identify a defensible new research capability for Scarbook.

## Executive answer

The official public page describes Track 3 as a new research tool that RYO does not already have, following the published tool specification, with a Python skill contract and honesty convention. It lists seven existing read-only tools. Scarbook implements `evidence_delta`, a read-only temporal comparison of two `analyze_token` observations.

## Claim-to-source ledger

| Claim | Source | Confidence | Note |
|---|---|---:|---|
| Track 3 requires a new research tool and published tool specification | [RYO-CHAN Hackathon 2026](https://ryobuild.com/) | High | Official public hackathon page, accessed 2026-09-08 |
| Existing surface includes `market_overview`, `scan_market`, `analyze_token`, `deep_analysis`, `compare_tokens`, `check_safety`, and `supported_tokens` | [RYO-CHAN Hackathon 2026](https://ryobuild.com/) | High | Official public tool list |
| RYO describes the surface as read-only and emphasizes missing-data honesty | [RYO-CHAN Hackathon 2026](https://ryobuild.com/) | High | Official public page |

## Evidence gap

The machine-readable organizer submission schema was not retrievable from the public page during research. The implementation therefore exposes a standard JSON-RPC MCP `tools/list`/`tools/call` surface and includes an explicit local `skill.json` contract, but does not claim organizer-schema validation.
