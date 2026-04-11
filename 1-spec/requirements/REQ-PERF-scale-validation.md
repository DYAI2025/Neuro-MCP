# REQ-PERF-scale-validation

**Status:** Draft
**Priority:** Should-have
**Type:** Performance
**Source:** [[1-spec/goals/GOAL-production-readiness|GOAL-production-readiness]]

## Description

The system must have reproducible benchmarks proving refresh/search/reconcile behavior across vault sizes (1k, 10k, 50k notes) with documented latency budgets and resource footprints. Watcher must survive burst changes without unbounded backlog.

## Acceptance Criteria (maps to tasks 66-70)

- [ ] TASK-benchmark-fixtures: deterministic fixtures for 1k, 10k, 50k notes/chunks
- [ ] TASK-refresh-search-benchmarks: refresh/search/reconcile/bootstrap benchmarked across fixture sizes
- [ ] TASK-watcher-storm-tests: burst file changes → backlog recovers without OOM
- [ ] TASK-memory-footprint-report: measured memory/storage footprint for indexes, tx tables, graph
- [ ] TASK-performance-budget-doc: acceptable latency/error budgets per command/mode documented

## Related Artifacts

Goal: [[1-spec/goals/GOAL-production-readiness|GOAL-production-readiness]]
Constraint: [[1-spec/constraints/CON-offline-first|CON-offline-first]]
