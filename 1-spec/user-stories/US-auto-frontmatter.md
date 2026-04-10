# US-auto-frontmatter

**Description**: As a knowledge worker, I want new and existing notes to automatically receive correct frontmatter (type, status, decay_class, last_verified, created) so that the freshness/decay mechanism works immediately — even when NeuroMCP is added to an existing project.

**Status**: Draft

**Priority**: Must-have

**Source stakeholder**: [[1-spec/stakeholders|STK-knowledge-worker]], [[1-spec/stakeholders|STK-developer]]

## Acceptance Criteria

- [ ] Folder-to-type mapping is configurable in config.yaml via `folder_type_map` field
- [ ] New notes without frontmatter get frontmatter added based on folder mapping (type, status: active, decay_class, last_verified: today, created: today)
- [ ] Existing notes with incomplete frontmatter get missing fields added; existing fields are never overwritten
- [ ] All NeuroMCP-written frontmatter includes `_neuro_mcp_enriched: true` and `_neuro_mcp_last: <ISO timestamp>`
- [ ] Enrichment runs on watcher trigger (live) and during `index` command (batch for existing vaults)
- [ ] Notes in folders not in the mapping get sensible defaults (type: note, decay_class: 30d)

## Related Artifacts

- Goals: [[1-spec/goals/GOAL-bidirectional-memory|GOAL-bidirectional-memory]], [[1-spec/goals/GOAL-context-bootstrap|GOAL-context-bootstrap]]
- Constraints: [[1-spec/constraints/CON-no-auto-delete|CON-no-auto-delete]], [[1-spec/constraints/CON-backwards-compatible|CON-backwards-compatible]]
