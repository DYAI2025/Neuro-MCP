# REQ-OBS-pipeline-metrics

**Status:** Draft
**Priority:** Should-have
**Type:** Observability
**Source:** [[1-spec/goals/GOAL-watcher-pipeline|GOAL-watcher-pipeline]]

## Description

The system shall track per-stage metrics (count of items processed, duration in milliseconds, error count) for each pipeline stage (STC, labile, auto-reconcile) and surface them in `digest()` and `brain_status` output, so operators can verify pipeline health and diagnose slow or failing stages.

## Acceptance Criteria

- [ ] Each pipeline stage records: stage name, items_processed, duration_ms, error_count
- [ ] Metrics from the most recent refresh are stored on the service instance
- [ ] `DigestReport` includes a `pipeline_stages` field: list of per-stage metric dicts
- [ ] `brain_status` / digest output shows stage timings and counts
- [ ] When a stage raises, its error_count increments but does not block other stages (already implemented)
- [ ] Metrics are reset on each refresh (represent the latest run, not cumulative)

## Related Artifacts

Goal: [[1-spec/goals/GOAL-watcher-pipeline|GOAL-watcher-pipeline]]
Constraint: [[1-spec/constraints/CON-backwards-compatible|CON-backwards-compatible]]
