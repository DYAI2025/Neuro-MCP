# Architecture

## System Overview

NeuroMCP is a local knowledge engine and MCP server that keeps semantic notes (the "brain") aligned with the codebase they describe. It uses neuro-inspired concepts -- freshness decay, reconsolidation, synaptic tagging, phasic/tonic modes -- to maintain knowledge integrity over time.

### 6-Layer Target Architecture

| Layer | Purpose | Current Status |
|-------|---------|----------------|
| **1. Ingestion** | Scan brain vault and codebase, parse frontmatter, chunk code, build DocumentRecords | Implemented (`notes.py`, `codebase.py`, `frontmatter.py`, `writer.py`) |
| **2. Knowledge Graph** | Store documents, compute embeddings, enable hybrid search | Implemented (`storage.py`, `embeddings.py`, `hybrid_embeddings.py`, `search.py`). Edge/relationship layer is implicit (via `linked_paths`, `claimed_dependencies`) -- no explicit graph store yet |
| **3. Verification** | Freshness decay, source-file existence checks, interference detection | Implemented (`freshness.py`, `interference.py`, `gc.py`). Claim-level verification is not yet implemented |
| **4. Reconsolidation** | Mark labile notes on contradiction, synaptic tagging promotions | Partially implemented (`reconsolidation.py`, `synaptic_tagging.py`). Review transactions (approve/reject cycle) not yet built |
| **5. Agent Interface** | MCP tools + CLI + HTTP transport | Implemented (`server.py`, `cli.py`). 10 MCP tools, 12 CLI subcommands, stdio + streamable-http transport |
| **6. Operations** | File watcher, GC, digest, mode detection | Implemented (`watcher.py`, `gc.py`, `git_utils.py`). Auto-watch via `watchfiles` with debounced re-index |

---

## Component Diagram

```
src/neuro_mcp/
+-- config.py            Settings (Pydantic): brain_root, code_root, weights, auth, etc.
+-- models.py            Domain models: DocumentRecord, NoteMetadata, SearchResult,
|                        ReconcileReport, GarbageCollectionReport, DigestReport, ChangeSet
+-- service.py           NeuroMCPService -- central orchestrator, holds all subsystems
|
+-- notes.py             scan_brain_documents(): walk brain_root, parse frontmatter,
|                        compute freshness, emit DocumentRecord + NoteMetadata
+-- codebase.py          scan_code_documents(): walk code_root, chunk files, extract
|                        package manifests (dependencies)
+-- frontmatter.py       parse_markdown_note() / dump_markdown_note() -- YAML frontmatter I/O
+-- writer.py            write_note() -- create/update brain notes with proper frontmatter
|
+-- storage.py           Repository (SQLite): persist DocumentRecords by DocKind
+-- embeddings.py        TfidfEmbedder: scikit-learn TF-IDF vectorizer, cosine scoring,
|                        joblib persistence
+-- hybrid_embeddings.py HybridEmbedder: wraps TfidfEmbedder + optional sentence-transformers
|                        model; weighted combination of TF-IDF and semantic scores
|
+-- search.py            rank_documents() / rank_documents_hybrid(): 4-signal weighted ranking
|                        dedupe_note_results(): remove duplicate sections from same note
+-- text_utils.py        tokenize(), keyword_score() -- lexical scoring utilities
+-- freshness.py         compute_freshness(): decay model (immutable/current/aging/stale/missing)
|                        freshness_bonus(): numeric bonus per FreshnessState
+-- reconcile.py         reconcile_results(): cross-check brain vs code, find contradictions
+-- reconsolidation.py   apply_reconsolidation(): mark notes labile when contradictions exist
+-- synaptic_tagging.py  evaluate_promotions(): promote inbox notes when correlated code changes
+-- interference.py      check_interference(): pairwise cosine similarity, merge/cross-link candidates
+-- gc.py                build_gc_report() / execute_gc_actions(): garbage collection
+-- git_utils.py         detect_mode(): phasic/tonic via git diff file count
+-- watcher.py           watch_forever(): async file watcher (watchfiles) with debounced refresh
|
+-- server.py            create_mcp_app(): FastMCP app with 10 tools, 1 resource, 1 prompt
|                        create_http_app(): Starlette wrapper with auth + health endpoints
+-- cli.py               CLI entry point: 12 subcommands via argparse
```

---

## Data Flows

### Indexing: `service.refresh()`

```
brain_root/                              code_root/
    |                                        |
    v                                        v
scan_brain_documents()                 scan_code_documents()
  - walk .md files                       - walk source files (by extension)
  - parse_markdown_note()                - chunk by chunk_lines/chunk_overlap
  - compute_freshness()                  - extract package manifests
  - build DocumentRecord + NoteMetadata  - build DocumentRecord
    |                                        |
    v                                        v
repo.replace_kind(BRAIN, docs)         repo.replace_kind(CODE, docs)
    |                                        |
    +----------+-----------------------------+
               |
               v
    brain_hybrid.fit(contents)     code_hybrid.fit(contents)
        |                              |
        v                              v
    brain_embedder.save()          code_embedder.save()
    (brain_index.joblib)           (code_index.joblib)
```

Both document sets are stored in `documents.sqlite3`. The TF-IDF matrices and optional sentence-transformer embeddings are cached in `.joblib` files. On next startup, `service.load()` restores from persisted state without re-scanning.

### Search: `service.search_brain()` / `service.search_codebase()`

```
query (str)
    |
    v
hybrid_embedder.score(query)
    |
    +-- TF-IDF cosine similarity (tfidf_weight * score)
    +-- Semantic cosine similarity (semantic_weight * score, if model loaded)
    |
    v
rank_documents_hybrid()
    |
    For each document, compute:
      relevance = semantic_weight * combined_semantic
               + lexical_weight  * keyword_score(query, content, path)
               + freshness_weight * freshness_bonus(state)
               + precision_weight * source_precision
    |
    v
sort by relevance descending, take top_k
    |
    v (brain only)
dedupe_note_results()  -- keep highest-scoring section per owner_id
    |
    v
list[SearchResult]
```

Default weights (configurable in Settings):
- `semantic_weight`: 0.55
- `lexical_weight`: 0.20
- `freshness_weight`: 0.15
- `precision_weight`: 0.10

Hybrid embedding weights:
- `semantic_model_weight`: 0.65 (sentence-transformers)
- `tfidf_model_weight`: 0.35 (TF-IDF)

### Reconciliation: `service.reconcile()`

```
query
    |
    +---> search_brain(query)  ----> brain_results
    +---> search_codebase(query) --> code_results
    |
    v
reconcile_results(brain_results, code_results, manifests, mode)
    |
    For each brain result:
      1. Check claimed_dependencies against actual manifests
         -> missing claims = contradiction
      2. Check source_files_exist flag
         -> missing files = contradiction
      3. Check freshness state
         -> stale/missing_sources = contradiction
    |
    v
    If contradictions exist:
      source_of_truth = "code"
    Else:
      source_of_truth = "brain+code"
    |
    v
    Query-specific recommendations:
      - architecture/adr/decision -> prefer stable CA3-style notes
      - bug/fix/sprint/todo -> prefer fresh CA1-style notes
    |
    v
ReconcileReport { query, source_of_truth, mode, brain_results,
                  code_results, contradictions, recommendations }
```

---

## Integration Points

### MCP Transport

- **stdio**: `FastMCP.run(transport="stdio")` -- standard MCP stdio protocol, used by Claude Desktop and similar clients
- **streamable-http**: Starlette app via `StreamableHTTPSessionManager`, served by uvicorn. Endpoints:
  - `POST /mcp` -- MCP protocol endpoint (configurable via `mcp_path` setting)
  - Origin guard middleware (checks `allowed_origins`)
  - Optional bearer token auth (`BearerAuthMiddleware`, constant-time comparison via `hmac.compare_digest`)

### File Watcher

- Uses `watchfiles` (`awatch`) to monitor both `brain_root` and `code_root`
- Debounce interval: `watch_debounce_seconds` (default 5s)
- Refresh runs in thread pool (`run_in_executor`) to keep event loop responsive
- Enabled via `auto_watch` setting (default `True`)

### Git Integration

- `git_utils.detect_mode()`: runs `git diff --name-only HEAD~1 HEAD` in `code_root`
- If changed files >= `phasic_change_threshold` (default 20): **TONIC** mode (high volatility)
- Otherwise: **PHASIC** mode (normal, incremental changes)
- Mode influences GC recommendations and reconciliation advice

### Security

- Data directory permissions check on init (warns if world-writable, since joblib uses pickle)
- Path traversal prevention in `brain_get_note` and `write_note` (`.is_relative_to()`)
- Bearer token auth for HTTP transport (optional, uses `SecretStr`)
- OAuth2 protected resource metadata endpoint (`/.well-known/oauth-protected-resource`)
