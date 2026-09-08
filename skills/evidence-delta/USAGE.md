# Evidence Delta usage

The skill is exposed through the Scarbook MCP endpoint:

```json
{
  "jsonrpc": "2.0",
  "id": "delta-1",
  "method": "tools/call",
  "params": {
    "name": "evidence_delta",
    "arguments": {"symbol": "SOL"}
  }
}
```

It is also available as REST at `POST /api/skill/evidence-delta` with body `{"symbol":"SOL"}`.
