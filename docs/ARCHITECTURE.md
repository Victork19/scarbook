# Architecture

```text
RYO live research
      ↓
RyoClient → normalizer → canonical hash → Evidence Receipt
                                      ↓
                              Agent proposal
                                      ↓ commit
                              Decision Ledger
                                      ↓ fresh T1
                         deterministic contradiction engine
                                      ↓
                       Evidence-Bound Constraint compiler
                                      ↓
                            fresh T2 session + gate
                                      ↓ blocked
                                bounded replan
```

The backend is deliberately small: FastAPI, Pydantic, httpx, and SQLite. The action gate is a pure function over an action and active constraints, which makes the key safety property testable without an LLM or network.

State transitions are persisted in the `sessions.status` column: `session_started`, `decision_proposed`, `committed`, `contradiction_checked`, `constraint_active`, and `final_decision`.

