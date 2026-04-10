# GOAL-reconsolidation-workflow

**Description**: When brain notes contradict code, the system transitions them through a persistent state machine (active → labile → reviewed → restabilized/superseded) with full audit trail.

**Status**: Draft

**Priority**: Must-have

**Source stakeholder**: [STK-ai-agent](../stakeholders.md), [STK-developer](../stakeholders.md)

## Success Criteria

- [ ] reconcile() creates a reconsolidation_tx record when contradiction exceeds threshold
- [ ] Affected notes get status: labile with labile_since and evidence fields in frontmatter
- [ ] Resolution paths exist: restabilize (update + verify) or supersede (link replacement)
- [ ] All transitions are logged in audit trail

## Related Artifacts

- Requirements: REQ-F-reconsolidation-transactions
