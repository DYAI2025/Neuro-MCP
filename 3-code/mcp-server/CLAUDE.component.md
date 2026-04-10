# MCP Server

**Responsibility**: Expose core engine functionality as MCP tools over stdio and streamable-HTTP transports. Handle authentication, origin validation, and health endpoints.

**Technology**: Python, FastMCP, Starlette, uvicorn

## Interfaces

- MCP protocol with AI clients (Claude Desktop, Cursor, custom agents): 9+ tools, 1 resource, 1 prompt
- HTTP endpoints: /healthz, /readyz, /mcp, /.well-known/oauth-protected-resource
- Python class API with core-engine: imports NeuroMCPService

## Source Files

- `src/neuro_mcp/server.py` -- MCP app builder, tool definitions, middleware
- `src/neuro_mcp/cli.py` -- CLI entry point, config loading, serve command

## Design References

- [[2-design/api-design|API Design]]
- [[2-design/architecture|Architecture]]
