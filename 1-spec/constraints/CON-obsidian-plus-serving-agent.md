# CON-obsidian-plus-serving-agent

**Status:** Draft
**Category:** Technical
**Source Stakeholder:** [[1-spec/stakeholders|STK-developer]]

## Description

NeuroMCP operates with Obsidian (or any markdown vault) as the knowledge substrate plus a serving agent (Claude Code, Claude Desktop, or custom MCP client) that reads/writes via the MCP protocol. The system does not require Obsidian-specific plugins — it works with raw markdown files.

## Rationale

Decoupling from Obsidian plugins ensures portability. Any markdown folder works. The MCP protocol is the integration boundary, not Obsidian APIs.

## Impact

- No Obsidian plugin dependencies
- All vault interaction via filesystem (reading) and frontmatter writing
- MCP protocol is the only integration contract with AI clients
