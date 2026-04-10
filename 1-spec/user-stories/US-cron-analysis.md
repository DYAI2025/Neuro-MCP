# US-cron-analysis

**Description**: As a knowledge worker, I want a CLI command that runs reconciliation, interference check, and digest in one pass and writes results as a summary note so that the system stays healthy even when the live watcher is not running.

**Status**: Draft

**Priority**: Should-have

**Source stakeholder**: [[1-spec/stakeholders|STK-developer]], [[1-spec/stakeholders|STK-knowledge-worker]]

## Acceptance Criteria

- [ ] CLI command: `neuro-mcp --config ... cron-analyze` runs once and exits (no daemon)
- [ ] Executes in order: reconcile (all indexed topics), check-interference, digest
- [ ] Writes a summary note to `00-inbox/neuro-mcp-analysis-<YYYY-MM-DD>.md`
- [ ] Summary note has frontmatter: type: inbox, decay_class: 7d, source_type: neuro-mcp-cron, _neuro_mcp_enriched: true
- [ ] Summary body includes: stale count, labile count, contradictions found, interference pairs, top risks, recommended actions
- [ ] Scheduleable via system cron (e.g. `*/30 * * * * neuro-mcp --config ... cron-analyze`)
- [ ] If watcher is also running, cron-analyze does not conflict (both are safe to run concurrently due to refresh lock)

## Related Artifacts

- Goals: [[1-spec/goals/GOAL-watcher-pipeline|GOAL-watcher-pipeline]], [[1-spec/goals/GOAL-context-bootstrap|GOAL-context-bootstrap]]
- Constraints: [[1-spec/constraints/CON-offline-first|CON-offline-first]]
