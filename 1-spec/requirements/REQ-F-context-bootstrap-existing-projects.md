# REQ-F-context-bootstrap-existing-projects

**Status:** Draft
**Priority:** Must-have
**Type:** Functional
**Source:** [[1-spec/goals/GOAL-context-bootstrap|GOAL-context-bootstrap]]

## Description

The system shall perform an initial context reconstruction pass before executing substantive work on a non-empty project, collecting project structure, dependencies, semantic relations, and prior development history.

## Acceptance Criteria

- [ ] Given an existing project, when NeuroMCP is initialized, it collects and organizes project context (notes, code structure, manifests, recent git history)
- [ ] Given incomplete context, the reconstruction explicitly records unresolved gaps rather than assuming certainty
- [ ] Given a project with pre-existing artifacts, subsequent actions reference the reconstructed context baseline

## Related Artifacts

Goal: [[1-spec/goals/GOAL-context-bootstrap|GOAL-context-bootstrap]]
