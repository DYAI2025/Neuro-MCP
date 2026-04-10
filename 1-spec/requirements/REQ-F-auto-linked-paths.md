# REQ-F-auto-linked-paths

**Status:** Draft
**Priority:** Must-have
**Type:** Functional
**Source:** US-auto-linked-paths

## Description

The system shall scan note content for references to code files, classes, functions, and other notes, then write discovered references to the `linked_paths` frontmatter field.

## Acceptance Criteria

- [ ] Scan note body for: filenames with code extensions, class/function identifiers, note references
- [ ] Match detected identifiers against code index (chunked blocks) and brain index
- [ ] Write matched paths to `linked_paths` in frontmatter (append-only, preserve manual entries)
- [ ] Mark enriched notes with `_neuro_mcp_enriched: true`
- [ ] Runs after each index/refresh cycle
- [ ] Uses code index for class/function matching (not naive text grep)

## Related Artifacts

Goal: [[1-spec/goals/GOAL-labile-auto-marking|GOAL-labile-auto-marking]]
User Story: [[1-spec/user-stories/US-auto-linked-paths|US-auto-linked-paths]]
Constraint: [[1-spec/constraints/CON-offline-first|CON-offline-first]]
