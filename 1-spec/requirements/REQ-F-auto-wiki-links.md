# REQ-F-auto-wiki-links

**Status:** Draft
**Priority:** Must-have
**Type:** Functional
**Source:** US-auto-wiki-links

## Description

The system shall automatically discover semantically related notes and set bidirectional wiki-links in the `related_notes` frontmatter field, enabling Obsidian graph visualization of knowledge structure.

## Acceptance Criteria

- [ ] After each index/refresh, compute pairwise semantic similarity for all brain notes
- [ ] Notes with similarity > configurable threshold (default 0.7) get `related_notes` frontmatter entries
- [ ] Links are bidirectional: both notes in a pair receive the link
- [ ] Existing manual `related_notes` entries are preserved (append-only)
- [ ] Wiki-link format: `[[relative/path/to/note]]` (Obsidian-native)
- [ ] Threshold is configurable via `auto_link_threshold` in config.yaml

## Related Artifacts

Goal: [[1-spec/goals/GOAL-bidirectional-memory|GOAL-bidirectional-memory]]
User Story: [[1-spec/user-stories/US-auto-wiki-links|US-auto-wiki-links]]
Constraint: [[1-spec/constraints/CON-offline-first|CON-offline-first]]
