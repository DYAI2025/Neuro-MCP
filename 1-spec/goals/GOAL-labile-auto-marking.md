# GOAL-labile-auto-marking

**Description**: Notes whose linked source files no longer exist are automatically marked labile when auto_mark_labile is enabled, so agents see invalidated knowledge immediately.

**Status**: Draft

**Priority**: Must-have

**Source stakeholder**: [STK-ai-agent](../stakeholders.md)

## Success Criteria

- [ ] When auto_mark_labile: true, refresh() checks linked_paths existence
- [ ] Notes with missing files get status: labile with reason logged
- [ ] When disabled (default), behavior unchanged — report only

## Related Artifacts

- Requirements: REQ-F-labile-auto-mark
