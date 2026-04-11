# REQ-OPS-migration-compatibility

**Status:** Draft
**Priority:** Must-have
**Type:** Operations
**Source:** [[1-spec/goals/GOAL-production-readiness|GOAL-production-readiness]]

## Description

Schema changes, new persistent tables, and new frontmatter fields must upgrade cleanly from older versions. Old repo state must start on a new runtime without data or interpretability loss.

## Acceptance Criteria (maps to tasks 55-59)

- [ ] TASK-schema-versioning: schema_version tracked in storage backend
- [ ] TASK-storage-migration-framework: lightweight migration runner for new tables/columns
- [ ] TASK-frontmatter-field-compat: compatibility policy for new frontmatter fields (labile_since, source_type, supersedes, etc.)
- [ ] TASK-upgrade-fixture-tests: tests verify old repo state upgrades cleanly to new runtime
- [ ] TASK-migration-runbook: rollback/backup/migration docs in 4-deploy/runbooks/

## Related Artifacts

Goal: [[1-spec/goals/GOAL-production-readiness|GOAL-production-readiness]]
Constraint: [[1-spec/constraints/CON-backwards-compatible|CON-backwards-compatible]]
