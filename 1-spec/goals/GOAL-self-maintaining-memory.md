# GOAL-self-maintaining-memory

**Status:** Draft
**Priority:** Must-have
**Source Stakeholder:** STK-developer, STK-knowledge-worker

## Description

Make the knowledge base self-maintaining: inbox notes get promoted or archived automatically based on salience, usage, and code corroboration. Monthly homeostasis prevents unbounded growth. GC applies real mutations, not just reports.

## Success Criteria

- [ ] STC promotion queue promotes inbox notes corroborated by code changes within 48h window
- [ ] Monthly homeostasis job renormalizes weights and demotes unused long-tail notes
- [ ] gc --apply actually mutates frontmatter status (not just report)
- [ ] auto_mark_labile config setting has real runtime effect
- [ ] Digest shows promotion candidates, homeostasis effects, and GC actions

## Related Artifacts

Requirements: _none yet_
