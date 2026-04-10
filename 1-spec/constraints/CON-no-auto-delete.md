# CON-no-auto-delete

**Status:** Approved
**Category:** Operational
**Source Stakeholder:** STK-developer

## Description

NeuroMCP must never auto-delete note files. GC returns archive candidates first; content mutation requires explicit --apply flag. Reconsolidation may change status in frontmatter but must not silently rewrite note body text outside clearly marked draft sections.

## Rationale

Core design principle: the system may change status, may suggest, but must not silently overwrite human-written content. Trust is the product's foundation.

## Impact

All reconsolidation, GC, and interference resolution features must be two-stage: auto-state transitions yes, human-approved content mutation only.
