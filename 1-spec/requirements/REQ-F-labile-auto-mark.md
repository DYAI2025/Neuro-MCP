# REQ-F-labile-auto-mark

**Status:** Draft
**Priority:** Must-have
**Type:** Functional
**Source:** [[1-spec/goals/GOAL-labile-auto-marking|GOAL-labile-auto-marking]]

## Description

The auto_mark_labile config setting (already in config.example.yaml) must have real runtime effect. When enabled, notes whose linked_paths reference deleted files are automatically marked status: labile.

## Acceptance Criteria

- [ ] When auto_mark_labile: true, refresh() checks linked_paths existence
- [ ] Notes with missing linked files get status: labile written to frontmatter
- [ ] The change is logged with reason (linked file deleted: path/to/file.ts)
- [ ] When auto_mark_labile: false (default), behavior is unchanged (report only)

## Related Artifacts

Goal: [[1-spec/goals/GOAL-labile-auto-marking|GOAL-labile-auto-marking]]
Constraint: [[1-spec/constraints/CON-backwards-compatible|CON-backwards-compatible]]
