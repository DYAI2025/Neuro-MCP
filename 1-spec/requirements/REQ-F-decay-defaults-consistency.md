# REQ-F-decay-defaults-consistency

**Status:** Draft
**Priority:** Must-have
**Type:** Functional
**Source:** GOAL-knowledge-discipline-engine

## Description

get_note() must use the same type-based decay defaults as the indexer. Currently it falls back to a hard 30d default, diverging from the documented type-based defaults (inbox=7d, bug=14d, architecture=90d, adr=immutable).

## Acceptance Criteria

- [ ] get_note() resolves decay_class using the same logic as scan_brain_documents()
- [ ] Both share a single DEFAULT_DECAY_BY_TYPE mapping (DRY)
- [ ] Notes without explicit decay_class get the type-based default, not hard 30d
- [ ] Existing tests for freshness scoring still pass

## Related Artifacts

Goal: GOAL-knowledge-discipline-engine
Constraint: CON-backwards-compatible
