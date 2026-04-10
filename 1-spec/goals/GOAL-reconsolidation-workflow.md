# GOAL-reconsolidation-workflow

**Description**: When brain notes contradict code, the system transitions them through a persistent state machine (active → labile → reviewed → restabilized/superseded) with full audit trail.

**Status**: Draft

**Priority**: Must-have

**Source stakeholder**: [[1-spec/stakeholders|STK-ai-agent]], [[1-spec/stakeholders|STK-developer]]

## Success Criteria

- [ ] reconcile() creates a reconsolidation_tx record when contradiction exceeds threshold
- [ ] Affected notes get status: labile with labile_since and evidence fields in frontmatter
- [ ] Resolution paths exist: restabilize (update + verify) or supersede (link replacement)
- [ ] All transitions are logged in audit trail

## Related Artifacts

- Requirements: [[1-spec/requirements/REQ-F-reconsolidation-transactions|REQ-F-reconsolidation-transactions]], [[1-spec/requirements/REQ-F-decay-defaults-consistency|REQ-F-decay-defaults-consistency]]
