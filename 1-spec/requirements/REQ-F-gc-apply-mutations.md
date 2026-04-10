# REQ-F-gc-apply-mutations

**Status:** Draft
**Priority:** Must-have
**Type:** Functional
**Source:** GOAL-gc-real-mutations

## Description

gc --apply must actually mutate note frontmatter (update status field) instead of only reporting candidates. The mutation must be idempotent and auditable.

## Acceptance Criteria

- [ ] gc --apply writes status: archived to frontmatter of notes meeting archive criteria
- [ ] Each mutation is logged with timestamp, reason, and previous status
- [ ] gc without --apply remains a dry run (report only, no mutations)
- [ ] Mutations are idempotent (running twice produces same result)

## Related Artifacts

Goal: GOAL-gc-real-mutations
Constraint: CON-no-auto-delete
