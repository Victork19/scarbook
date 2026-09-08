#!/usr/bin/env bash
set -Eeuo pipefail

API_URL="${API_URL:-http://127.0.0.1:8000}"
SESSION_ID="${1:-sess-004}"

echo "Committing decision for ${SESSION_ID}"
curl -sS -X POST "${API_URL}/api/decision/commit" \
  -H 'Content-Type: application/json' \
  --data-binary @- <<JSON
{"session_id":"${SESSION_ID}","decision":{"thesis":"SOL accumulate with RSI14 63.3.","side":"long","size":0.25,"confidence":0.6,"evidence_used":["verdict: accumulate","rsi14: 63.3"]}}
JSON
echo

echo "Requesting second live read"
curl -sS -X POST "${API_URL}/api/recheck" \
  -H 'Content-Type: application/json' \
  --data-binary @- <<JSON
{"session_id":"${SESSION_ID}"}
JSON
echo

echo "Starting fresh session"
curl -sS -X POST "${API_URL}/api/session/new" \
  -H 'Content-Type: application/json' \
  --data-binary @- <<JSON
{"symbol":"SOL","parent_session_id":"${SESSION_ID}"}
JSON
echo
