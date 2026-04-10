# REQ-F-bidirectional-memory

**Status:** Draft
**Priority:** Must-have
**Type:** Functional
**Source:** [[1-spec/goals/GOAL-bidirectional-memory|GOAL-bidirectional-memory]]

## Description

AI sessions must be able to write findings back into the brain vault via brain_ingest_note, and code changes detected by the file watcher must auto-trigger reconciliation of affected brain notes.

## Acceptance Criteria

- [ ] brain_ingest_note creates/updates notes with valid frontmatter (title, type, decay_class, last_verified, source_type)
- [ ] Ingested notes are immediately indexed and searchable without manual re-index
- [ ] Notes track which source created them via source_type field (e.g. "agent-session", "manual", "codebase-analysis")
- [ ] Code changes detected by watcher trigger reconcile() on notes whose linked_paths overlap with changed files
- [ ] Auto-reconciliation results (contradictions found) are visible in digest() and brain_status

## Related Artifacts

Goal: [[1-spec/goals/GOAL-bidirectional-memory|GOAL-bidirectional-memory]]
Constraint: [[1-spec/constraints/CON-no-auto-delete|CON-no-auto-delete]]
