# GOAL-watcher-pipeline

**Description**: Wire the file watcher into a complete orchestration pipeline: change → debounce → refresh → STC check → labile marking → reconsolidation trigger, with each stage independently configurable.

**Status**: Draft

**Priority**: Must-have

**Source stakeholder**: [STK-developer](../stakeholders.md)

## Success Criteria

- [ ] watch_forever() chains: refresh → STC → auto_mark_labile → reconcile trigger
- [ ] Each stage toggled on/off in config.yaml
- [ ] Errors in one stage do not block subsequent stages
- [ ] Pipeline stages are logged for observability

## Related Artifacts

- Requirements: REQ-F-watcher-orchestration
