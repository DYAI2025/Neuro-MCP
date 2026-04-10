# GOAL-gc-real-mutations

**Description**: gc --apply actually mutates note frontmatter (sets status: archived) instead of only reporting candidates. Mutations are idempotent and auditable.

**Status**: Draft

**Priority**: Must-have

**Source stakeholder**: [[1-spec/stakeholders|STK-developer]]

## Success Criteria

- [ ] gc --apply writes status: archived to qualifying notes' frontmatter
- [ ] Each mutation logged with timestamp, reason, previous status
- [ ] gc without --apply remains dry-run (no changes)
- [ ] Running twice produces identical result

## Related Artifacts

- Requirements: [[1-spec/requirements/REQ-F-gc-apply-mutations|REQ-F-gc-apply-mutations]]
