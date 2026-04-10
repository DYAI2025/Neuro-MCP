# Core Engine

**Responsibility**: Indexing, search, freshness scoring, reconciliation, reconsolidation, synaptic tagging, garbage collection, and interference management.

**Technology**: Python 3.11+, SQLite, TF-IDF (scikit-learn), sentence-transformers (optional)

## Interfaces

- Python class API with mcp-server: NeuroMCPService methods (search_brain, search_code, reconcile, digest, gc, get_note, get_related, ingest, check_interference, mode_detect)

## Source Files

- `src/neuro_mcp/service.py` -- orchestrator
- `src/neuro_mcp/storage.py` -- SQLite persistence
- `src/neuro_mcp/search.py` -- hybrid search scoring
- `src/neuro_mcp/freshness.py` -- decay and freshness model
- `src/neuro_mcp/reconcile.py` -- brain vs code cross-check
- `src/neuro_mcp/reconsolidation.py` -- mismatch-triggered state transitions
- `src/neuro_mcp/synaptic_tagging.py` -- STC promotion logic
- `src/neuro_mcp/interference.py` -- duplicate/conflict detection
- `src/neuro_mcp/notes.py` -- brain vault scanner
- `src/neuro_mcp/codebase.py` -- code scanner and manifest parser
- `src/neuro_mcp/embeddings.py` -- TF-IDF + semantic embedders
- `src/neuro_mcp/models.py` -- data models
- `src/neuro_mcp/config.py` -- Settings model
- `src/neuro_mcp/watcher.py` -- file system watcher
- `src/neuro_mcp/git_utils.py` -- git diff analysis
- `src/neuro_mcp/writer.py` -- frontmatter writer

## Requirements Addressed

| Requirement | Priority | Summary |
|-------------|----------|---------|
| [[1-spec/requirements/REQ-F-reconsolidation-transactions|REQ-F-reconsolidation-transactions]] | Must-have | Persistent reconsolidation transactions |
| [[1-spec/requirements/REQ-F-gc-apply-mutations|REQ-F-gc-apply-mutations]] | Must-have | GC applies real frontmatter mutations |
| [[1-spec/requirements/REQ-F-stc-promotion-queue|REQ-F-stc-promotion-queue]] | Must-have | STC-based inbox promotion |
| [[1-spec/requirements/REQ-F-labile-auto-mark|REQ-F-labile-auto-mark]] | Must-have | Auto-mark labile on missing linked files |
| [[1-spec/requirements/REQ-F-watcher-orchestration|REQ-F-watcher-orchestration]] | Must-have | Full watcher pipeline orchestration |
| [[1-spec/requirements/REQ-F-decay-defaults-consistency|REQ-F-decay-defaults-consistency]] | Must-have | Consistent type-based decay defaults |

## Design References

- [[2-design/architecture|Architecture]]
- [[2-design/data-model|Data Model]]
- [[2-design/api-design|API Design]]
