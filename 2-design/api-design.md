# API Design

## MCP Tools (v1 -- implemented)

All tools are registered via `FastMCP` in `server.py`. They return `dict[str, Any]` serialized as JSON.

### 1. search_brain

Search the second brain vault. Returns results with freshness, precision, and source-file existence flags.

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `query` | `str` | required | Search query |
| `top_k` | `int` | `5` | Max results |

**Returns:** `{ query: str, results: SearchResult[] }`

### 2. search_codebase

Search the codebase. Code results are always marked as current/active with precision 1.0.

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `query` | `str` | required | Search query |
| `top_k` | `int` | `5` | Max results |

**Returns:** `{ query: str, results: SearchResult[] }`

### 3. reconcile_brain_with_code

Cross-check brain notes against the codebase. Identifies contradictions (missing dependencies, missing source files, stale notes).

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `query` | `str` | required | Topic to reconcile |
| `top_k` | `int` | `5` | Results per source |

**Returns:** `ReconcileReport { query, source_of_truth, mode, brain_results, code_results, contradictions, recommendations }`

### 4. freshness_digest

Return current freshness and volatility digest for the knowledge base.

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| (none) | -- | -- | -- |

**Returns:** `DigestReport { generated_at, mode, total_notes, stale_notes, labile_notes, missing_source_notes, top_risks, next_actions }`

### 5. run_garbage_collection

Evaluate stale notes and missing source links. Does not delete files by default.

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `dry_run` | `bool` | `True` | If true, report only; if false, update frontmatter |

**Returns:** `GarbageCollectionReport { dry_run, mode, items, total_notes, stale_count, missing_sources_count, archived_candidates }`

### 6. brain_get_note

Retrieve a specific brain note by its relative path within the vault.

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `path` | `str` | required | Relative path within brain_root |

**Returns:** `{ found: bool, path: str, title?: str, content?: str, metadata?: { note_type, status, decay_class, source_precision, freshness, stale_reasons, tags, last_verified, linked_paths, source_files_exist } }`

Path traversal outside brain_root is rejected.

### 7. brain_get_related

Find notes semantically related to a given note using embedding similarity.

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `path` | `str` | required | Relative path of the anchor note |
| `top_k` | `int` | `5` | Max related notes |

**Returns:** `{ found: bool, path: str, related: [{ title, path, relevance, freshness, snippet }] }`

### 8. brain_ingest_note

Write a new note or update an existing one in the brain vault.

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `relative_path` | `str` | required | Target path within brain_root |
| `title` | `str` | required | Note title |
| `content` | `str` | required | Markdown body |
| `note_type` | `str` | `"note"` | Note type |
| `tags` | `list[str]?` | `None` | Tags |
| `decay_class` | `str` | `"30d"` | Decay class |
| `source_precision` | `float` | `0.7` | Confidence |
| `claimed_dependencies` | `list[str]?` | `None` | Package dependencies |

**Returns:** `{ status: "created"|"updated", path: str, title: str }`

Triggers re-index on next access (`_loaded = False`).

### 9. brain_status

Return overall brain health overview.

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| (none) | -- | -- | -- |

**Returns:** `{ total_notes: int, by_type: {}, by_status: {}, by_freshness: {}, mode: str, has_semantic: bool, recommendations: str[] }`

### 10. check_interference

Detect overlapping or near-duplicate brain notes using embedding similarity.

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| (none) | -- | -- | -- |

**Returns:** `{ candidates: [{ note_a, note_b, similarity, action, reason }], threshold: float, total_docs: int }`

Actions: `merge` (same note sections overlap) or `cross_link` (different notes overlap). Safety cap at 1000 documents (O(n^2)).

---

## MCP Resource (v1)

### brain://digest/stale

Returns the freshness digest as JSON. Useful for MCP resource subscriptions.

---

## MCP Prompt (v1)

### grounded_answer_prompt

| Param | Type | Description |
|-------|------|-------------|
| `question` | `str` | The user's question |

Returns a prompt instructing the agent to use `search_brain` and `search_codebase`, prefer code when they disagree, and mention freshness/precision.

---

## Proposed v2 MCP Tools

### verify_claim

Verify a specific claim from a brain note against the codebase.

| Param | Type | Description |
|-------|------|-------------|
| `note_path` | `str` | Path to the note containing the claim |
| `claim_text` | `str` | The specific claim to verify |

**Returns:** `{ verified: bool, evidence: [{ source, snippet, confidence }], contradictions: str[] }`

### explain_contradictions

Given a reconcile report, generate a human-readable explanation of all contradictions.

| Param | Type | Description |
|-------|------|-------------|
| `query` | `str` | The reconcile query |

**Returns:** `{ explanations: [{ note_path, contradiction, explanation, suggested_fix }] }`

### propose_note_patch

Generate a patch for a brain note to resolve contradictions with the codebase.

| Param | Type | Description |
|-------|------|-------------|
| `note_path` | `str` | Path to the note to patch |
| `contradictions` | `list[str]` | Contradictions to address |

**Returns:** `{ tx_id: str, original_content: str, proposed_content: str, diff: str }`

### approve_reconsolidation

Approve or reject a reconsolidation transaction. Applies the patch if approved.

| Param | Type | Description |
|-------|------|-------------|
| `tx_id` | `str` | Transaction ID from propose_note_patch |
| `verdict` | `str` | `"approve"`, `"reject"`, `"merge"` |

**Returns:** `{ tx_id: str, status: str, note_path: str }`

---

## CLI Commands

All commands accept `--config <path>` or `--brain-root / --code-root` flags. Optional `--data-dir` and `--bearer-token`.

| Command | Arguments | Description |
|---------|-----------|-------------|
| `index` | -- | Full re-scan and re-index of brain and code |
| `search-brain` | `<query> [--top-k N]` | Search brain vault |
| `search-code` | `<query> [--top-k N]` | Search codebase |
| `reconcile` | `<query> [--top-k N]` | Cross-check brain vs code |
| `digest` | -- | Freshness and volatility report |
| `gc` | `[--apply]` | Garbage collection (dry-run by default) |
| `status` | -- | Brain health overview |
| `check-interference` | -- | Find overlapping notes |
| `get-note` | `<path>` | Retrieve specific note |
| `get-related` | `<path> [--top-k N]` | Find related notes |
| `ingest` | `<path> --title T --content C [--type T] [--tags ...] [--decay-class D]` | Write/update a note |
| `serve` | `[--transport stdio\|streamable-http] [--host H] [--port P]` | Start MCP server |

All commands output JSON to stdout.

---

## HTTP Endpoints

Exposed by `create_http_app()` when using `--transport streamable-http`.

| Path | Method | Description |
|------|--------|-------------|
| `/healthz` | `GET` | Liveness probe. Returns `{"status": "ok"}` |
| `/readyz` | `GET` | Readiness probe. Returns `{"status": "ready"}` |
| `/mcp` | `POST` | MCP protocol endpoint (configurable via `mcp_path` setting). Handled by `StreamableHTTPSessionManager` |
| `/.well-known/oauth-protected-resource` | `GET` | OAuth2 protected resource metadata. Returns `{ resource, authorization_servers, scopes_supported, bearer_methods_supported }` |

### Middleware Stack

1. **OriginGuardMiddleware** -- Rejects requests to `/mcp` from disallowed origins (checks `Origin` header against `allowed_origins`)
2. **BearerAuthMiddleware** (optional, only when `bearer_token` is set) -- Requires `Authorization: Bearer <token>` header for `/mcp` requests. Uses constant-time comparison. Returns `401` with `WWW-Authenticate` header pointing to metadata URL.
