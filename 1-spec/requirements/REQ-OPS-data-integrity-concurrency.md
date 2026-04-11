# REQ-OPS-data-integrity-concurrency

**Status:** Draft
**Priority:** Must-have
**Type:** Operations
**Source:** [[1-spec/goals/GOAL-production-readiness|GOAL-production-readiness]]

## Description

All frontmatter and storage mutations must be safe under concurrent refresh, watcher, GC, ingest, and reconcile operations. No silent corruption, no interleaved partial writes, no duplicated state transitions on repeated events.

## Acceptance Criteria (maps to tasks 50-54)

- [ ] TASK-frontmatter-write-locking: writer.py mutations use file-level locking or atomic temp-file replace
- [ ] TASK-storage-frontmatter-transaction-order: defined mutation ordering (storage update → frontmatter write → log write)
- [ ] TASK-concurrent-refresh-search-tests: stress tests cover refresh/search/reconcile/gc overlap without corruption
- [ ] TASK-watcher-debounce-backpressure: watch_forever uses bounded event queue with backpressure policy
- [ ] TASK-idempotent-state-transition-guards: labile/archive/promote transitions are idempotent under repeated events

## Related Artifacts

Goal: [[1-spec/goals/GOAL-production-readiness|GOAL-production-readiness]]
Constraint: [[1-spec/constraints/CON-no-auto-delete|CON-no-auto-delete]]
