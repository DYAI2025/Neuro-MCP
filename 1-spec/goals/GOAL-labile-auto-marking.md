# GOAL-labile-auto-marking

**Description**: Notes whose linked source files no longer exist are automatically marked labile when auto_mark_labile is enabled, so agents see invalidated knowledge immediately.

**Status**: Draft

**Priority**: Must-have

**Source stakeholder**: [[1-spec/stakeholders|STK-ai-agent]]

## Success Criteria

- [ ] When auto_mark_labile: true, refresh() checks linked_paths existence
- [ ] Notes with missing files get status: labile with reason logged
- [ ] When disabled (default), behavior unchanged — report only

## Related Artifacts

- Requirements: [[1-spec/requirements/REQ-F-labile-auto-mark|REQ-F-labile-auto-mark]]
