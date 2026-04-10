# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Installation

```bash
# Core only (no MCP server, no semantic embeddings)
pip install .

# With MCP server support (required for `serve` subcommand)
pip install '.[mcp]'

# With semantic embeddings via sentence-transformers
pip install '.[semantic]'

# Dev dependencies (pytest)
pip install '.[dev]'
```

## Running tests

```bash
# All tests
pytest

# Single test file
pytest tests/test_freshness.py

# Single test by name
pytest tests/test_freshness.py::test_stale_note
```

pytest is configured in `pyproject.toml`: `pythonpath = ["src"]`, `testpaths = ["tests"]`.

## CLI commands

All commands take `--config config.yaml` or `--brain-root / --code-root` flags.

```bash
neuro-mcp --config config.example.yaml index
neuro-mcp --config config.example.yaml search-brain "query"
neuro-mcp --config config.example.yaml search-code "query"
neuro-mcp --config config.example.yaml reconcile "query"
neuro-mcp --config config.example.yaml digest
neuro-mcp --config config.example.yaml gc            # dry run
neuro-mcp --config config.example.yaml gc --apply    # execute
neuro-mcp --config config.example.yaml status
neuro-mcp --config config.example.yaml check-interference
neuro-mcp --config config.example.yaml get-note path/to/note.md
neuro-mcp --config config.example.yaml get-related path/to/note.md

# MCP server
neuro-mcp --config config.example.yaml serve --transport stdio
neuro-mcp --config config.example.yaml serve --transport streamable-http --host 127.0.0.1 --port 8000
```

## Architecture

`NeuroMCPService` (`service.py`) is the central orchestrator. It holds:
- `Repository` (SQLite) — persists `DocumentRecord` rows by `DocKind` (BRAIN or CODE)
- `TfidfEmbedder` — deterministic, offline-safe vector store (saves to `.joblib`)
- `HybridEmbedder` — wraps TF-IDF + optional `sentence-transformers` model; weighted combination

**Data flow for indexing (`refresh`):**
1. `scan_brain_documents` (`notes.py`) — walks `brain_root`, parses YAML frontmatter, computes `FreshnessState`, builds `DocumentRecord` + `NoteMetadata`
2. `scan_code_documents` (`codebase.py`) — walks `code_root`, chunks files by `chunk_lines`/`chunk_overlap`, extracts package manifests
3. Both document sets are written to SQLite via `repo.replace_kind()`
4. Both `HybridEmbedder`s are fitted on the new document content

**Search scoring** is a weighted sum of four signals: `semantic_weight`, `lexical_weight`, `freshness_weight`, `precision_weight` (must sum to ~1.0).

**Reconcile** cross-checks brain search results against code results and marks contradictions. Code always wins as source of truth when they disagree.

**Mode detection** (`git_utils.py`): counts recently changed files in `code_root` via `git diff`. If changes exceed `phasic_change_threshold`, the system enters `TONIC` mode (major volatility).

**MCP server** (`server.py`): builds a `FastMCP` app exposing 9 tools + 1 resource + 1 prompt. For HTTP transport, wraps in a Starlette app with `OriginGuardMiddleware` and optional `BearerAuthMiddleware`. MCP imports are lazy so the package works without the optional dependency.

## Key design constraints

- GC never auto-deletes files — it returns archive candidates only (`dry_run=True` by default)
- `brain_get_note` validates paths are within `brain_root` to prevent traversal (checked via `.is_relative_to()`)
- Search weights in `Settings` are validated to sum to ~1.0 at model instantiation
- `immutable_note_types` (default: `["adr"]`) skip freshness decay entirely
- The default embedder is TF-IDF; semantic embeddings are opt-in via `pip install '.[semantic]'`

## Configuration

`Settings` (`config.py`) can be loaded from YAML or JSON via `Settings.from_file()`. The two required fields are `brain_root` and `code_root`. Data (SQLite + joblib index files) is stored in `data_dir` (default: `.neuro_mcp/`).

See `config.example.yaml` for all available knobs.
