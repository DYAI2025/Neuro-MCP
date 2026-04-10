# CON-backwards-compatible

**Status:** Approved
**Category:** Technical
**Source Stakeholder:** STK-developer

## Description

v2 extensions must not break existing config.yaml files, CLI commands, or MCP tool signatures. New fields in frontmatter must have sensible defaults. New SQLite tables must be created via migration, not by dropping existing data.

## Rationale

Existing users with working setups must not be forced to reconfigure or reindex from scratch.

## Impact

All schema changes require migration logic. New frontmatter fields default gracefully. New CLI subcommands are additive.
