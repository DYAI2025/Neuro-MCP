# Neuro MCP Server

A production-oriented MCP server and local knowledge engine for a "second brain" that keeps semantic notes useful over time instead of turning into stale lore.

## What it does

- indexes markdown notes with YAML frontmatter
- indexes the codebase in chunked form
- computes freshness from `last_verified`, `decay_class`, and linked source paths
- treats code as source of truth when notes and manifests disagree
- exposes MCP tools for:
  - `search_brain`
  - `search_codebase`
  - `reconcile_brain_with_code`
  - `freshness_digest`
  - `run_garbage_collection`
- supports stdio for local MCP use and Streamable HTTP for remote deployment
- adds HTTP origin validation and optional bearer-token protection

## Core design

The system is derived from seven neuro-inspired rules:

1. reconsolidation instead of overwrite
2. precision weighting
3. synaptic tagging and capture
4. molecular timers
5. CA3 / CA1 split
6. interference management
7. phasic / tonic volatility modes

See `docs/neuro_transfer.md`.

## Frontmatter schema

```yaml
---
title: RingStory component
type: component
status: active
created: 2026-04-10
last_verified: 2026-04-10
decay_class: 30d
source_precision: 0.8
source_type: codebase-analysis
linked_paths:
  - src/components/RingStory.tsx
claimed_dependencies:
  - react
tags:
  - component
  - ringstory
---
```

## Why code wins

Notes capture rationale, intent, and semantic memory.
Code captures current implementation state.
When they disagree, this server returns the contradiction and marks code as source of truth.

## Installation

Local core only:

```bash
pip install .
```

With MCP support:

```bash
pip install '.[mcp]'
```

## Quick start

Index the bundled demo data:

```bash
neuro-mcp --config config.example.yaml index
```

Search the brain:

```bash
neuro-mcp --config config.example.yaml search-brain "tech stack"
```

Search the code:

```bash
neuro-mcp --config config.example.yaml search-code "RingStory component"
```

Reconcile both:

```bash
neuro-mcp --config config.example.yaml reconcile "Are we using react?"
```

Get freshness digest:

```bash
neuro-mcp --config config.example.yaml digest
```

Run a safe garbage-collection audit:

```bash
neuro-mcp --config config.example.yaml gc
```

## Run as MCP server

### Stdio

```bash
neuro-mcp --config config.example.yaml serve --transport stdio
```

### Streamable HTTP

```bash
neuro-mcp --config config.example.yaml serve --transport streamable-http --host 127.0.0.1 --port 8000
```

This exposes:
- `GET /healthz`
- `GET /readyz`
- `GET /.well-known/oauth-protected-resource`
- `POST/GET /mcp`

## Security notes

For remote deployment:

- bind to `127.0.0.1` by default
- validate `Origin`
- require bearer auth or front the server with an OAuth-aware reverse proxy
- prefer an external auth server for enterprise deployments

## Production notes

This repository is production-oriented, but there are three intentional conservative choices:

1. It does not auto-delete note files.
   Garbage collection returns archive candidates first.

2. Contradiction detection is explicit-first.
   Missing linked files and missing claimed dependencies are first-class.
   Free-text contradiction mining is intentionally conservative.

3. The default local embedder is TF-IDF based.
   It is deterministic and offline-safe. If you need stronger semantic retrieval,
   swap in a richer embedding provider behind the same service boundary.

## Suggested deployment layout

- process 1: `neuro-mcp ... serve --transport streamable-http`
- process 2: scheduled `neuro-mcp ... index`
- process 3: scheduled `neuro-mcp ... gc`
- reverse proxy: TLS, OAuth or JWT validation, audit logs

## MCP client notes

The implementation targets the current official MCP Python SDK line. The core package stays importable without the optional MCP dependency so that indexing and audits can run in plain Python environments.

## License

MIT
