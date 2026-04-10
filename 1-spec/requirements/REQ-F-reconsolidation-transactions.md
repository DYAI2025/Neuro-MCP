# REQ-F-reconsolidation-transactions

**Status:** Draft
**Priority:** Must-have
**Type:** Functional
**Source:** GOAL-reconsolidation-workflow

## Description

When reconcile() detects a contradiction above the configured threshold, the system must create a persistent reconsolidation transaction that transitions the affected note from active to labile. The transaction records: evidence (which code/manifest contradicts), reason, timestamp, and resolution deadline.

## Acceptance Criteria

- [ ] reconcile() creates a reconsolidation_tx record in SQLite when contradiction_score > threshold
- [ ] Affected note's frontmatter status is updated to labile with labile_since and labile_reasons
- [ ] labile notes are downweighted in search results (freshness score <= 0.40)
- [ ] digest() and brain_status show count of open reconsolidation transactions
- [ ] Resolution path exists: restabilize (update note + set current) or supersede (link to replacement note)
- [ ] All state transitions are logged in an audit trail

## Related Artifacts

Goal: GOAL-reconsolidation-workflow
Constraint: CON-no-auto-delete
