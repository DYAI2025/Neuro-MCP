# US-auto-linked-paths

**Description**: As a knowledge worker, I want notes to automatically get `linked_paths` in frontmatter when they reference code files, classes, functions, or other notes so that reconciliation and labile-marking work on real data.

**Status**: Draft

**Priority**: Must-have

**Source stakeholder**: [[1-spec/stakeholders|STK-ai-agent]], [[1-spec/stakeholders|STK-developer]]

## Acceptance Criteria

- [ ] Note content is scanned for: file names (.py, .ts, .tsx, .js, .go, etc.), class names, function names, and note references
- [ ] Detected references are matched against the code index (chunked code blocks with identifiers) and brain index
- [ ] Matched references are written to `linked_paths` in frontmatter
- [ ] Existing manual `linked_paths` entries are preserved — only new matches are appended
- [ ] `_neuro_mcp_enriched: true` is set on enriched notes
- [ ] Class and function name matching uses the code index (not just filename grep)
- [ ] Enrichment runs after each index/refresh cycle

## Related Artifacts

- Goals: [[1-spec/goals/GOAL-labile-auto-marking|GOAL-labile-auto-marking]], [[1-spec/goals/GOAL-reconsolidation-workflow|GOAL-reconsolidation-workflow]]
- Constraints: [[1-spec/constraints/CON-offline-first|CON-offline-first]]
