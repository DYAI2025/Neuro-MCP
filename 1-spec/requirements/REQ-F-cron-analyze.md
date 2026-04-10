# REQ-F-cron-analyze

**Status:** Draft
**Priority:** Should-have
**Type:** Functional
**Source:** US-cron-analysis

## Description

The system shall provide a `cron-analyze` CLI command that runs reconciliation, interference check, and digest in one pass and writes a summary note to the brain vault.

## Acceptance Criteria

- [ ] CLI subcommand `cron-analyze` runs reconcile + interference + digest sequentially
- [ ] Writes summary note to `00-inbox/neuro-mcp-analysis-<YYYY-MM-DD>.md` with type: inbox, decay_class: 7d
- [ ] Summary includes: stale count, labile count, contradictions, interference pairs, risks, actions
- [ ] Note frontmatter includes `source_type: neuro-mcp-cron` and `_neuro_mcp_enriched: true`
- [ ] Safe to run concurrently with watcher (uses existing refresh lock)
- [ ] Exits after single run (no daemon mode)

## Related Artifacts

Goal: [[1-spec/goals/GOAL-watcher-pipeline|GOAL-watcher-pipeline]]
User Story: [[1-spec/user-stories/US-cron-analysis|US-cron-analysis]]
Constraint: [[1-spec/constraints/CON-offline-first|CON-offline-first]]
