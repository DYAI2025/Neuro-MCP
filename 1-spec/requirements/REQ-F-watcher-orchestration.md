# REQ-F-watcher-orchestration

**Status:** Draft
**Priority:** Must-have
**Type:** Functional
**Source:** [[1-spec/goals/GOAL-watcher-pipeline|GOAL-watcher-pipeline]]

## Description

Wire watcher.py into a complete orchestration pipeline: file change -> debounce -> refresh -> STC check -> optional auto_mark_labile -> optional reconsolidation trigger. Currently the watcher only calls refresh().

## Acceptance Criteria

- [ ] watch_forever() calls refresh() then synaptic_tagging_check() on each change batch
- [ ] If auto_mark_labile is enabled, labile marking runs after refresh
- [ ] If reconsolidation is enabled, contradiction check runs after refresh
- [ ] Each stage is independently configurable (on/off in config.yaml)
- [ ] Errors in any stage are logged but do not block subsequent stages

## Related Artifacts

Goal: [[1-spec/goals/GOAL-watcher-pipeline|GOAL-watcher-pipeline]]
