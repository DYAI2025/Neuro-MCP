# GOAL-stc-promotion

**Description**: Inbox notes (7d decay) are promoted to 30d when correlated code changes occur within the 48h STC window, preventing valuable short-lived notes from expiring prematurely.

**Status**: Draft

**Priority**: Must-have

**Source stakeholder**: [STK-developer](../stakeholders.md), [STK-knowledge-worker](../stakeholders.md)

## Success Criteria

- [ ] synaptic_tagging.py runs on each file change event via refresh() or watcher
- [ ] Promoted notes get decay_class updated in frontmatter with log entry
- [ ] Only 7d (inbox) notes are eligible
- [ ] digest() shows promotion candidates and recent promotions

## Related Artifacts

- Requirements: REQ-F-stc-promotion-queue
