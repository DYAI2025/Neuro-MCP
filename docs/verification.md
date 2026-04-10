# Verification

## Scope (2026-04-10)

Validation focus for MCP conversation access to these 10 tools:

1. `search_brain`
2. `search_codebase`
3. `reconcile_brain_with_code`
4. `brain_get_note`
5. `brain_get_related`
6. `brain_ingest_note`
7. `brain_status`
8. `freshness_digest`
9. `run_garbage_collection`
10. `check_interference`

## Code-level analysis

- All 10 tools are registered in `create_mcp_app()` via `@mcp.tool()` wrappers and routed to `NeuroMCPService`. 
- Tool handlers return JSON-serializable payloads (typically `model_dump(mode="json")` for typed models).
- The server module lazily imports MCP SDK (`from mcp.server import FastMCP`) so the core package can still be imported when MCP extras are absent.

## Added automated check

- Added `tests/test_server_tools.py`.
- The test injects a fake `mcp.server.FastMCP`, builds an app via `create_mcp_app()`, verifies all 10 tool names, and runs one smoke invocation per tool.

## Local checks completed in this environment

- `pytest -q tests/test_server_tools.py ...` -> **failed during collection** because required Python dependencies are not installed (`pydantic`, `joblib`, etc.).
- `uv sync --frozen --extra dev` -> **failed** because network/proxy blocks fetching `pytest` transitive dependencies.

## Important caveat

This container currently lacks core runtime/test dependencies and cannot download them due to proxy restrictions, so pytest-based execution could not be completed here. The added test is ready to run in a fully provisioned environment.
