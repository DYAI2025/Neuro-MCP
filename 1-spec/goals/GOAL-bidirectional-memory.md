# GOAL-bidirectional-memory

**Description**: NeuroMCP is not read-only — AI sessions write findings back as notes via brain_ingest_note, and code changes auto-trigger reconciliation of affected brain notes.

**Status**: Draft

**Priority**: Must-have

**Source stakeholder**: [[1-spec/stakeholders|STK-ai-agent]], [[1-spec/stakeholders|STK-developer]]

## Success Criteria

- [ ] brain_ingest_note creates/updates notes with proper frontmatter and triggers re-indexing
- [ ] Code changes detected by watcher auto-reconcile affected brain notes
- [ ] Session findings persisted as notes are immediately searchable
- [ ] Notes track which agent session created them (source_type field)

## Related Artifacts

- Requirements: [[1-spec/requirements/REQ-F-bidirectional-memory|REQ-F-bidirectional-memory]]
