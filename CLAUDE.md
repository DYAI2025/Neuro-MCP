# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Persistent Memory (NeuroMCP — use this first)

This repo uses NeuroMCP on itself (self-referential). The repo's own SDLC artifacts (goals, requirements, ADRs, architecture docs) are the brain; its Python source is the code.

```bash
# Self-referential: search this repo's own specs, ADRs, plans as brain notes
uv run neuro-mcp --config config-self.yaml search-brain "<topic>"

# Search this repo's own Python source as code
uv run neuro-mcp --config config-self.yaml search-code "<topic>"

# Cross-check: do the specs agree with the implementation?
uv run neuro-mcp --config config-self.yaml reconcile "<topic>"

# Full status (365 notes, phasic mode)
uv run neuro-mcp --config config-self.yaml status

# Re-index after changes
uv run neuro-mcp --config config-self.yaml index
```

Self-server runs on port 8767: `uv run neuro-mcp --config config-self.yaml serve --transport streamable-http --port 8767`

External brain vault (Obsidian) is still available via config-bazodiac.yaml (port 8766).

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

## Project Overview

NeuroMCP is a production-oriented MCP server and local knowledge engine that keeps semantic notes useful over time by connecting them to the codebase they describe. It uses neuro-inspired concepts (freshness decay, reconsolidation, synaptic tagging, phasic/tonic modes) to maintain knowledge integrity.

### Current State

The core system is stable (v1): dual brain/code indexing, freshness model, reconciliation, MCP tools, HTTP/stdio transport. Implementation plan created (2026-04-10): 6 phases, 48 tasks covering all 10 approved goals. Implementation progress: 19/50 tasks done. Phase 1 + 2 complete; Phase 3 code complete (runbook pending). Next: Phase 3 runbook, then Phase 4 (Reconsolidation Transactions). See `3-code/tasks.md`.

## SDLC Structure

This project uses the [AI SDLC Scaffold](https://github.com/pangon/ai-sdlc-scaffold) for AI-first development:

- `1-spec/` — WHAT and WHY: goals, requirements, constraints, user stories
- `2-design/` — HOW: architecture, data model, API design
- `3-code/` — BUILD: component directories, tasks, source code
- `4-deploy/` — SHIP: runbooks, deployment procedures
- `decisions/` — Decision records (DEC-*.md + history)
- `.claude/skills/SDLC-*/` — Claude skills for each SDLC phase

Skills: `/SDLC-init`, `/SDLC-elicit`, `/SDLC-design`, `/SDLC-decompose`, `/SDLC-implementation-plan`, `/SDLC-execute-next-task`, `/SDLC-fix`, `/SDLC-status`
