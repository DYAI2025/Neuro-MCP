# REQ-F-auto-frontmatter-enrichment

**Status:** Draft
**Priority:** Must-have
**Type:** Functional
**Source:** US-auto-frontmatter

## Description

The system shall automatically enrich notes with correct frontmatter based on a configurable folder-to-type mapping. New notes get full frontmatter; existing notes get missing fields added. All enrichments are marked with _neuro_mcp_enriched and timestamp.

## Acceptance Criteria

- [ ] `folder_type_map` config field maps folder prefixes to {type, decay_class} defaults
- [ ] Notes without frontmatter get complete frontmatter generated on index/refresh
- [ ] Notes with partial frontmatter get only missing fields added
- [ ] All NeuroMCP writes include `_neuro_mcp_enriched: true` and `_neuro_mcp_last` timestamp
- [ ] Enrichment is triggered by watcher (live) and index command (batch)
- [ ] Existing user-written frontmatter fields are never overwritten

## Related Artifacts

Goal: [[1-spec/goals/GOAL-bidirectional-memory|GOAL-bidirectional-memory]]
User Story: [[1-spec/user-stories/US-auto-frontmatter|US-auto-frontmatter]]
Constraint: [[1-spec/constraints/CON-no-auto-delete|CON-no-auto-delete]], [[1-spec/constraints/CON-backwards-compatible|CON-backwards-compatible]]
