# US-auto-wiki-links

**Description**: As a knowledge worker, I want NeuroMCP to automatically set wiki-links between semantically related notes in the frontmatter so that the Obsidian graph view shows the knowledge structure without manual linking.

**Status**: Draft

**Priority**: Must-have

**Source stakeholder**: [[1-spec/stakeholders|STK-knowledge-worker]], [[1-spec/stakeholders|STK-ai-agent]]

## Acceptance Criteria

- [ ] Related notes are stored as frontmatter field: `related_notes: ["[[path/to/note]]", ...]`
- [ ] Only notes with semantic similarity > 0.7 (configurable via `auto_link_threshold` in config.yaml) are linked
- [ ] Links are bidirectional: if Note A links to Note B, Note B also gets a link to Note A
- [ ] Existing manual entries in `related_notes` are preserved — NeuroMCP only appends, never removes
- [ ] `_neuro_mcp_last: <ISO timestamp>` is updated on each enrichment pass
- [ ] Obsidian graph view shows the auto-generated links as edges (wiki-links in YAML are natively supported)
- [ ] Enrichment runs after each index/refresh cycle

## Related Artifacts

- Goals: [[1-spec/goals/GOAL-bidirectional-memory|GOAL-bidirectional-memory]], [[1-spec/goals/GOAL-coherent-narrative|GOAL-coherent-narrative]]
- Constraints: [[1-spec/constraints/CON-no-auto-delete|CON-no-auto-delete]], [[1-spec/constraints/CON-offline-first|CON-offline-first]]
