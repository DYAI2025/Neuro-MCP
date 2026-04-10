# Neuro MCP — User Guide

A local knowledge engine that keeps markdown notes useful over time by connecting them to the codebase they describe.

---

## Table of Contents

- [Concept](#concept)
- [Installation](#installation)
- [Configuration](#configuration)
- [Starting the Server](#starting-the-server)
- [CLI Reference](#cli-reference)
- [MCP Tools Reference](#mcp-tools-reference)
- [Frontmatter Schema](#frontmatter-schema)
- [Decay Classes & Freshness](#decay-classes--freshness)
- [Modes: Phasic vs Tonic](#modes-phasic-vs-tonic)
- [Use Cases & Possibilities](#use-cases--possibilities)
- [Claude Desktop Integration](#claude-desktop-integration)
- [Multi-Project Setup](#multi-project-setup)
- [Troubleshooting](#troubleshooting)

---

## Concept

Neuro MCP runs two parallel indices:

- **Brain** — your markdown vault (Obsidian, plain files, etc.)
- **Code** — your codebase, chunked by lines

When you ask a question, both are searched and cross-checked. If a note claims a dependency that does not exist in your `package.json` or `pyproject.toml`, or references a file that has been deleted, the server surfaces the contradiction and marks code as the source of truth.

The system uses a **freshness model**: every note has a decay timer. Notes that haven't been verified in a while, or whose linked source files no longer exist, are flagged as stale. This prevents your knowledge base from silently lying to you.

---

## Installation

### Requirements

- Python 3.11+
- `uv` (recommended) or `pip`

### Core only (no MCP server, offline-safe)

```bash
pip install .
# or with uv:
uv sync
```

This gives you the `neuro-mcp` CLI for indexing and searching locally.

### With MCP server (HTTP + stdio transport)

```bash
pip install '.[mcp]'
# or:
uv sync --extra mcp
```

Adds `uvicorn`, `starlette`, and the MCP SDK. Required for `serve` subcommand.

### With semantic embeddings (better search quality)

```bash
pip install '.[semantic]'
# or:
uv sync --extra semantic
```

Downloads `sentence-transformers` (~400 MB). Enables the `all-MiniLM-L6-v2` model for hybrid TF-IDF + neural search. Without this, the server falls back to TF-IDF only — still usable, just less semantic.

### Full install

```bash
pip install '.[mcp,semantic]'
```

---

## Configuration

The server is configured via a YAML (or JSON) file. Minimum required fields:

```yaml
brain_root: /path/to/your/notes
code_root: /path/to/your/project
```

### Full reference

```yaml
# --- Required ---
brain_root: /Users/you/Obsidian/my-vault
code_root: /Users/you/Projects/my-project

# --- Storage ---
data_dir: .neuro_mcp           # where SQLite + index files are stored

# --- Code scanning ---
include_extensions:
  - .py
  - .ts
  - .tsx
  - .js
  - .jsx
  - .go
  - .rs
  - .md
  - .yaml
  - .toml

exclude_dirs:
  - .git
  - node_modules
  - dist
  - build
  - .next
  - __pycache__
  - .venv
  - archive

chunk_lines: 80                # lines per code chunk
chunk_overlap: 20              # overlap between chunks

# --- Search ---
search_top_k: 5
semantic_weight: 0.55          # weights must sum to 1.0
lexical_weight: 0.20
freshness_weight: 0.15
precision_weight: 0.10

# --- Hybrid embeddings ---
semantic_model: all-MiniLM-L6-v2
semantic_model_weight: 0.65
tfidf_model_weight: 0.35
# semantic_cache_dir: ~/.cache/sentence_transformers

# --- Freshness ---
similarity_threshold: 0.85     # for interference detection
stc_window_hours: 48           # synaptic tagging window
phasic_change_threshold: 20    # git file changes before switching to tonic mode
immutable_note_types:
  - adr                        # these note types never decay

# --- Server ---
mcp_server_name: NeuroMCP
mcp_path: /mcp
bind_host: 127.0.0.1
bind_port: 8000
allowed_origins:
  - http://localhost
  - https://localhost
# bearer_token: change-me-and-keep-secret
# external_auth_metadata_url: https://auth.example.com/.well-known/oauth-authorization-server

# --- File watcher ---
auto_watch: true
watch_debounce_seconds: 5.0
```

### Multiple projects

Create one config file per project:

```
config-bazodiac.yaml      → Bazodiac-WebApp/Astro-Noctum
config-deepagent.yaml     → Projects/DeepAgent
config-flashdoc.yaml      → Projects/FlashDoc
```

Each gets its own `data_dir` so the indices don't collide.

---

## Starting the Server

### One-time index (no server)

```bash
neuro-mcp --config config.yaml index
```

Walks `brain_root` and `code_root`, builds the SQLite document store and TF-IDF index. Run this after cloning or when you want to force a full re-index.

### stdio (for Claude Desktop / local MCP clients)

```bash
neuro-mcp --config config.yaml serve --transport stdio
```

The process speaks the MCP protocol over stdin/stdout. No network port needed.

### HTTP server (for remote clients or browser access)

```bash
neuro-mcp --config config.yaml serve --transport streamable-http --host 127.0.0.1 --port 8000
```

Endpoints exposed:
- `GET /healthz` — liveness probe
- `GET /readyz` — readiness probe
- `POST /mcp` — MCP tool calls
- `GET /.well-known/oauth-protected-resource` — OAuth metadata

### Background / production

```bash
# background with log file
neuro-mcp --config config.yaml serve --transport streamable-http > neuro-mcp.log 2>&1 &

# or with systemd (see deployment section)
```

### Without a config file (quick start)

```bash
neuro-mcp --brain-root ~/notes --code-root ~/project index
neuro-mcp --brain-root ~/notes --code-root ~/project search-brain "authentication flow"
```

---

## CLI Reference

All commands accept `--config <file>` or the pair `--brain-root` / `--code-root`.

| Command | What it does |
|---|---|
| `index` | Build / rebuild the full index from scratch |
| `search-brain <query>` | Search markdown notes with freshness and precision scoring |
| `search-code <query>` | Search code chunks — always returns current, source_of_truth=code |
| `reconcile <query>` | Cross-check brain vs code, surface contradictions |
| `digest` | Freshness overview: stale count, missing sources, next actions |
| `status` | Note counts by type, status, freshness + current mode |
| `gc` | Garbage collection audit (dry run by default) |
| `gc --apply` | Execute GC — updates status in frontmatter, does NOT delete files |
| `check-interference` | Find near-duplicate notes by embedding similarity |
| `get-note <path>` | Retrieve a note with full freshness metadata |
| `get-related <path>` | Find semantically related notes |
| `ingest --title T --content C <path>` | Write or update a note programmatically |

### Examples

```bash
# What does the app know about authentication?
neuro-mcp --config config.yaml search-brain "authentication JWT"

# What does the code actually do with authentication?
neuro-mcp --config config.yaml search-code "JWT token validation"

# Do the notes and code agree?
neuro-mcp --config config.yaml reconcile "authentication"

# How stale is the knowledge base?
neuro-mcp --config config.yaml digest

# Find overlapping notes that could be merged
neuro-mcp --config config.yaml check-interference

# Read one note including its freshness state
neuro-mcp --config config.yaml get-note "architecture/auth-design.md"

# Write a discovery back into the brain
neuro-mcp --config config.yaml ingest notes/finding.md \
  --title "JWT expiry bug" \
  --content "Token expiry is not validated server-side in the refresh endpoint." \
  --type bug \
  --decay-class 14d
```

---

## MCP Tools Reference

When connected via MCP (Claude Desktop, Cursor, etc.) these tools are available:

### `search_brain`

Search markdown notes. Returns relevance, freshness, source precision, and whether linked source files still exist.

```json
{ "query": "authentication flow", "top_k": 5 }
```

### `search_codebase`

Search code chunks. Code is always marked as source of truth with `freshness: current`.

```json
{ "query": "JWT token refresh", "top_k": 5 }
```

### `reconcile_brain_with_code`

Cross-checks both indices. Returns contradictions (missing dependencies, deleted source files, stale notes) and a `source_of_truth` verdict: `"code"` or `"brain+code"`.

```json
{ "query": "how does auth work", "top_k": 5 }
```

### `freshness_digest`

Returns an overview of the knowledge base health: total notes, stale count, labile count, missing source count, current mode, and recommended next actions.

```json
{}
```

### `run_garbage_collection`

Identifies notes that should be archived or have their status updated. Safe by default (`dry_run: true`).

```json
{ "dry_run": true }
```

### `brain_get_note`

Retrieve a specific note by relative path (relative to `brain_root`). Returns full content + all freshness metadata.

```json
{ "path": "architecture/component-overview.md" }
```

### `brain_get_related`

Find notes semantically related to a given note — useful for "what else is connected to this?"

```json
{ "path": "architecture/component-overview.md", "top_k": 5 }
```

### `brain_ingest_note`

Write or update a note in the vault. Use this to persist findings, decisions, or analysis results from a Claude conversation back into your knowledge base.

```json
{
  "relative_path": "discoveries/auth-finding.md",
  "title": "Auth endpoint missing rate limiting",
  "content": "The /api/login endpoint has no rate limiting...",
  "note_type": "bug",
  "decay_class": "14d",
  "tags": ["security", "auth"],
  "claimed_dependencies": ["express-rate-limit"]
}
```

### `brain_status`

Overview: note counts by type/status/freshness, current mode, whether semantic embeddings are active, and recommendations.

```json
{}
```

### `check_interference`

Finds near-duplicate brain notes above the similarity threshold. Returns merge or cross-link candidates.

```json
{}
```

---

## Frontmatter Schema

Every note Neuro MCP indexes should have YAML frontmatter:

```yaml
---
title: Auth Service Design
type: architecture-doc
status: active
created: 2026-01-15
last_verified: 2026-04-10
decay_class: 90d
source_precision: 0.9
source_type: codebase-analysis
linked_paths:
  - src/auth/service.ts
  - src/auth/middleware.ts
claimed_dependencies:
  - jsonwebtoken
  - express-rate-limit
tags:
  - auth
  - architecture
---
```

### Field reference

| Field | Type | Purpose |
|---|---|---|
| `title` | string | Display name |
| `type` | string | Note type (see decay defaults below) |
| `status` | `active` / `stale` / `labile` / `archived` | Current state |
| `created` | date | Creation date |
| `last_verified` | date | Last time you confirmed this is still true |
| `decay_class` | `7d` / `14d` / `30d` / `60d` / `90d` / `immutable` | How long before it goes stale |
| `source_precision` | 0.0–1.0 | How confident you are in this note (boosts search ranking) |
| `source_type` | string | How this was created (`manual`, `codebase-analysis`, etc.) |
| `linked_paths` | list | Paths in `code_root` that this note describes |
| `claimed_dependencies` | list | Packages this note says the project uses |
| `tags` | list | Free-form tags |

Notes without frontmatter are still indexed — they just get default freshness values.

---

## Decay Classes & Freshness

Every note type has a default decay window. After that window, the note becomes **stale** unless `last_verified` is updated.

| Note type | Default decay |
|---|---|
| `adr` | immutable (never decays) |
| `architecture-doc` / `architecture` | 90 days |
| `tech` | 60 days |
| `component` / `api-doc` / `workflow` / `note` | 30 days |
| `bug` / `bug-fix` | 14 days |
| `inbox` | 7 days |

### Freshness states

| State | Meaning | Search bonus |
|---|---|---|
| `immutable` | ADR or explicitly marked — never expires | 0.95 |
| `current` | Verified recently, source files exist | 1.00 |
| `aging` | Past 50% of decay window | 0.75 |
| `stale` | Past full decay window | 0.40 |
| `missing_sources` | `linked_paths` files no longer exist | 0.25 |

Freshness is factored into search ranking via `freshness_weight`. Stale notes still appear in results — they are just ranked lower.

### To refresh a note

Update `last_verified` in frontmatter:

```yaml
last_verified: 2026-04-10
```

Or use the `ingest` tool / CLI to rewrite the note entirely.

---

## Modes: Phasic vs Tonic

Neuro MCP checks `git diff HEAD~1 HEAD` to count recently changed files.

| Mode | Condition | Effect |
|---|---|---|
| **Phasic** | < 20 changed files | Normal search, standard reconcile |
| **Tonic** | ≥ 20 changed files | Major volatility detected — reconcile recommends full audit, GC is more aggressive |

The threshold is configurable: `phasic_change_threshold: 20`.

In tonic mode, `brain_status` and `freshness_digest` append: *"Tonic mode: major code changes detected — run full reconcile audit."*

---

## Use Cases & Possibilities

### 1. Ask Claude about your codebase with grounded context

Connect via Claude Desktop (see below). Then ask naturally:

> "How does the payment flow work? Are the notes about it still accurate?"

Claude will call `reconcile_brain_with_code`, compare your architecture notes against the actual code, and tell you where they diverge.

### 2. Catch stale documentation before it causes bugs

```bash
neuro-mcp --config config.yaml digest
```

```json
{
  "stale_notes": 30,
  "missing_source_notes": 3,
  "next_actions": [
    "Run freshness verification on stale notes.",
    "Run garbage collection and relink missing source paths."
  ]
}
```

Run this before onboarding a new team member or before a big refactor.

### 3. Dependency reconciliation

If a note claims `"claimed_dependencies": ["react-query"]` but your `package.json` no longer has it, `reconcile` surfaces this as a contradiction and marks the note as labile.

### 4. Find and merge duplicate notes

```bash
neuro-mcp --config config.yaml check-interference
```

Returns pairs of notes above the similarity threshold with recommended action: `merge` (same note, overlapping sections) or `cross_link` (different notes that cover the same ground).

### 5. Write discoveries back from Claude

During a debugging session, ask Claude to persist its findings:

> "Save what you found about the rate-limiting bug as a note."

Claude calls `brain_ingest_note` with `type: bug`, `decay_class: 14d`, and the relevant `claimed_dependencies`. The note appears in your vault immediately.

### 6. Architecture audit before a release

```bash
# What does the code say about auth?
neuro-mcp --config config.yaml search-code "authentication middleware"

# What do the notes say?
neuro-mcp --config config.yaml search-brain "authentication middleware"

# Where do they disagree?
neuro-mcp --config config.yaml reconcile "authentication middleware"
```

### 7. Garbage collection

```bash
# See what would be archived (safe, no changes)
neuro-mcp --config config.yaml gc

# Apply — updates status in frontmatter only, never deletes files
neuro-mcp --config config.yaml gc --apply
```

Inbox notes older than 7 days and bug notes older than 14 days become archive candidates.

### 8. Synaptic tagging (automatic promotion)

If an inbox note was created within the last 48 hours and its `linked_paths` overlap with files changed in recent git commits, it is promoted from `7d` to `30d` decay. This mirrors how the brain consolidates fresh memories that are correlated with active work.

---

## Claude Desktop Integration

### stdio (simplest)

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "neuro-mcp": {
      "command": "uv",
      "args": [
        "--directory",
        "/Users/benjaminpoersch/Obsidian_new/neuro_mcp/neuro_mcp_server_clean",
        "run",
        "neuro-mcp",
        "--config",
        "/Users/benjaminpoersch/Obsidian_new/neuro_mcp/neuro_mcp_server_clean/config.yaml",
        "serve",
        "--transport",
        "stdio"
      ]
    }
  }
}
```

### HTTP (already running)

If the server is already running at `http://127.0.0.1:8766`:

```json
{
  "mcpServers": {
    "neuro-mcp-bazodiac": {
      "url": "http://127.0.0.1:8766/mcp"
    }
  }
}
```

### Multiple projects at once

```json
{
  "mcpServers": {
    "neuro-bazodiac": {
      "url": "http://127.0.0.1:8766/mcp"
    },
    "neuro-deepagent": {
      "url": "http://127.0.0.1:8767/mcp"
    }
  }
}
```

Each project runs on its own port with its own config and data_dir.

---

## Multi-Project Setup

```bash
# Project 1 — Bazodiac
neuro-mcp --config config-bazodiac.yaml serve \
  --transport streamable-http --port 8766 &

# Project 2 — DeepAgent
neuro-mcp --config config-deepagent.yaml serve \
  --transport streamable-http --port 8767 &

# Project 3 — FlashDoc
neuro-mcp --config config-flashdoc.yaml serve \
  --transport streamable-http --port 8768 &
```

Each has its own `data_dir`, so the SQLite databases and joblib indices don't interfere.

---

## Troubleshooting

### `ModuleNotFoundError: No module named 'uvicorn'`

The MCP extra is not installed. Run:

```bash
uv sync --extra mcp
```

### `ModuleNotFoundError: No module named 'sentence_transformers'`

Optional — the server works without it (TF-IDF only). To enable semantic search:

```bash
uv sync --extra semantic
```

### Server starts but search returns no results

Run `index` first:

```bash
neuro-mcp --config config.yaml index
```

### `data_dir is world-writable` warning

The directory holding the index files is writable by all users. Fix:

```bash
chmod o-w /path/to/.neuro_mcp
```

### All notes show as stale

Notes without a `last_verified` field are immediately stale. Add the field to your note template. To bulk-update, run `gc --apply` which updates status in frontmatter, or add `last_verified` to your Obsidian template.

### Port already in use

Each project needs its own port. Use `bind_port` in the config or `--port` on the command line.

### Check what's running

```bash
# Health check
curl http://127.0.0.1:8766/healthz

# Status
neuro-mcp --config config-bazodiac.yaml status
```
