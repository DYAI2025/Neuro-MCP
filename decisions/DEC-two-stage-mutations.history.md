# DEC-two-stage-mutations — History

## 2026-04-10 — Initial Decision

**Context:** NeuroMCP v2 adds reconsolidation workflows that can modify notes. A clear boundary is needed between what the system may change autonomously and what requires human approval.

**Decision:** Two-stage mutations: auto-state transitions yes, content mutations only with explicit approval.

**Alternatives considered:**
- Full auto-mutation (rejected: breaks trust, users lose control of their notes)
- No auto-mutation (rejected: too manual, defeats the purpose of self-maintaining memory)
- Diff-based approval UI (deferred: good idea but too complex for v2 scope)

**Accepted by:** Developer (project owner)
