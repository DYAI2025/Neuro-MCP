# GOAL-context-bootstrap

**Description**: When NeuroMCP attaches to an existing project, it reconstructs enough semantic and historical context to avoid incoherent actions — before any substantive work begins.

**Status**: Draft

**Priority**: Must-have

**Source stakeholder**: [[1-spec/stakeholders|STK-team-onboarder]], [[1-spec/stakeholders|STK-ai-agent]]

## Success Criteria

- [ ] Initial index pass collects project structure, dependencies, architecture notes, and recent git history
- [ ] Unresolved gaps are explicitly recorded, not silently assumed
- [ ] Subsequent agent actions can reference the reconstructed context baseline

## Related Artifacts

- Requirements: [[1-spec/requirements/REQ-F-context-bootstrap-existing-projects|REQ-F-context-bootstrap-existing-projects]]
