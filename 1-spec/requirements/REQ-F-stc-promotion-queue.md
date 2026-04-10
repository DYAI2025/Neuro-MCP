# REQ-F-stc-promotion-queue

**Status:** Draft
**Priority:** Must-have
**Type:** Functional
**Source:** [[1-spec/goals/GOAL-stc-promotion|GOAL-stc-promotion]]

## Description

Implement a promotion queue based on Synaptic Tagging and Capture. Inbox notes created within the STC window (default 48h) whose linked_paths overlap with recently changed files (git diff) are promoted from 7d to 30d decay class.

## Acceptance Criteria

- [ ] synaptic_tagging.py is called from service.refresh() or watcher.py on each file change event
- [ ] Notes matching STC criteria have their decay_class updated in frontmatter
- [ ] Promotion is logged (which note, which overlapping files, old to new decay_class)
- [ ] digest() shows promotion candidates and recent promotions
- [ ] Only notes with decay_class: 7d (inbox) are eligible for promotion

## Related Artifacts

Goal: [[1-spec/goals/GOAL-stc-promotion|GOAL-stc-promotion]]
