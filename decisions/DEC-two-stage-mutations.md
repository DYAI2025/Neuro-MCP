# DEC-two-stage-mutations

**Status:** Active
**Date:** 2026-04-10
**Trigger:** When implementing any feature that modifies note content

## Decision

All mutations to note content follow a two-stage process:
1. Auto-state transitions — the system may change status in frontmatter (active -> labile -> stale -> archived)
2. Human-approved content mutation — the system must not silently rewrite note body text; it may only draft suggestions

## Rationale

Trust is the product's foundation. Users must be confident that their written content is not silently altered. Status metadata is system-owned; content is human-owned.

## Enforcement

- gc --apply may change status field but must not alter note body
- Reconsolidation may set status: labile but must not rewrite note content
- propose_note_patch (future) creates a draft, not an in-place edit

## Related Artifacts

- [[1-spec/goals/GOAL-gc-real-mutations|GOAL-gc-real-mutations]]
- [[1-spec/goals/GOAL-reconsolidation-workflow|GOAL-reconsolidation-workflow]]
- [[1-spec/constraints/CON-no-auto-delete|CON-no-auto-delete]]
