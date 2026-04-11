# REQ-OPS-observability-runtime-metrics

**Status:** Draft
**Priority:** Must-have
**Type:** Operations
**Source:** [[1-spec/goals/GOAL-production-readiness|GOAL-production-readiness]]

## Description

Runtime state must be visible via structured logs, counters, latency histograms, and expanded health signals. Operators need to see when the system drifts, stalls, fails, or tips into tonic mode.

## Acceptance Criteria (maps to tasks 60-65)

- [ ] TASK-structured-logging: standardized structured logs for refresh, reconcile, gc, watcher, ingest
- [ ] TASK-runtime-metrics-counters: counters for stale_count, labile_count, open_recon_tx, gc_mutations, watcher_errors
- [ ] TASK-latency-metrics: durations captured for refresh/search/reconcile/bootstrap
- [ ] TASK-health-expanded: /readyz and /healthz expose degraded-state indicators
- [ ] TASK-digest-ops-section: digest() includes errors, pending reviews, recent mutations, queue pressure
- [ ] TASK-observability-tests: verify metrics emitted, degraded state visible, logs include correlation fields

## Related Artifacts

Goal: [[1-spec/goals/GOAL-production-readiness|GOAL-production-readiness]]
Related: [[1-spec/requirements/REQ-OBS-pipeline-metrics|REQ-OBS-pipeline-metrics]]
