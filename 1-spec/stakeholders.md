# Stakeholders

## STK-developer

**Role:** Solo developer / project owner
**Perspective:** Builds and maintains NeuroMCP, uses it daily for own projects
**Key needs:** Fast iteration, reliable freshness model, MCP integration that works across all AI clients
**Communication:** Direct (user = developer)

## STK-ai-agent

**Role:** AI agent (Claude, Cursor, custom agents) consuming NeuroMCP tools
**Perspective:** Needs grounded, verified project knowledge to avoid hallucination
**Key needs:** Reliable search results, source-of-truth verdicts, contradiction detection, ability to persist findings
**Communication:** MCP protocol (stdio/HTTP)

## STK-knowledge-worker

**Role:** End user maintaining an Obsidian/markdown knowledge vault
**Perspective:** Wants notes to stay accurate without manual audit effort
**Key needs:** Automatic freshness tracking, stale note detection, duplicate management, low maintenance overhead
**Communication:** CLI, MCP tools via Claude Desktop

## STK-team-onboarder

**Role:** New team member joining a project that uses NeuroMCP
**Perspective:** Needs to quickly understand project architecture and decisions
**Key needs:** Reconciled brain+code search, current architecture notes, contradiction-free knowledge base
**Communication:** MCP tools, CLI
