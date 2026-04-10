# Verification

## Local checks completed in this environment

- `pytest -q` -> 4 tests passed
- `python -m py_compile` on all package files -> passed
- CLI smoke tests executed:
  - `index`
  - `search-brain "tech stack"`
  - `search-code "RingStory component"`
  - `reconcile "Are we using react?"`
  - `digest`
  - `gc`

## Important caveat

The optional `mcp` dependency is not installed in this container, so the MCP transport itself
was not executed here. The transport-facing modules compile and the core engine was tested.
