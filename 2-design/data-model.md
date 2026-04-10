# Data Model

## Core Domain Models

All models are defined in `src/neuro_mcp/models.py` using Pydantic `BaseModel`.

### DocumentRecord

The universal document unit stored in SQLite. Used for both brain notes and code chunks.

| Field | Type | Description |
|-------|------|-------------|
| `doc_id` | `str` | Primary key (deterministic hash or generated ID) |
| `kind` | `DocKind` | `"brain"` or `"code"` |
| `owner_id` | `str` | Groups sections of the same source file (e.g., same note path) |
| `path` | `str` | Absolute file path |
| `uri` | `str` | URI for MCP resource references |
| `title` | `str` | Human-readable title (from frontmatter or filename) |
| `content` | `str` | Full text content of the chunk |
| `snippet` | `str` | Shortened preview text |
| `line_start` | `int` | Start line in source file (default 1) |
| `line_end` | `int` | End line in source file (default 1) |
| `content_hash` | `str` | Hash of content for change detection |
| `metadata` | `dict[str, Any]` | Serialized as JSON; holds freshness, tags, note_type, source_precision, etc. |

### NoteMetadata

Extended metadata for brain notes. One per note file (not per chunk).

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `note_id` | `str` | -- | Unique identifier (typically relative path) |
| `title` | `str` | -- | Note title |
| `path` | `str` | -- | Relative path within brain_root |
| `note_type` | `str` | `"note"` | Type: `note`, `adr`, `architecture-doc`, `tech`, `component`, `api-doc`, `bug`, `bug-fix`, `workflow`, `inbox` |
| `status` | `NoteStatus` | `ACTIVE` | Lifecycle: `active`, `stale`, `labile`, `superseded`, `archived` |
| `created` | `datetime?` | `None` | Creation timestamp |
| `last_verified` | `datetime?` | `None` | Last verification/review date |
| `decay_class` | `str` | `"30d"` | TTL class: `immutable`, `90d`, `60d`, `30d`, `14d`, `7d` |
| `source_precision` | `float` | `0.5` | Confidence in the note's accuracy (0.0-1.0) |
| `source_type` | `str` | `"manual"` | How the note was created |
| `tags` | `list[str]` | `[]` | User-defined tags |
| `linked_paths` | `list[str]` | `[]` | Paths to source files this note describes |
| `claimed_dependencies` | `list[str]` | `[]` | Package dependencies the note claims exist |
| `linked_commits` | `list[str]` | `[]` | Git commit hashes associated with the note |
| `superseded_by` | `str?` | `None` | Path to the note that replaces this one |
| `source_files_exist` | `bool` | `True` | Whether all `linked_paths` exist on disk |
| `freshness` | `FreshnessState` | `CURRENT` | Computed freshness state |
| `stale_reasons` | `list[str]` | `[]` | Why the note is stale (e.g., `"older_than_30d"`, `"linked_source_missing"`) |
| `extra` | `dict[str, Any]` | `{}` | Catch-all for additional frontmatter fields |

### SearchResult

Returned from search operations. Extends DocumentRecord fields with scoring.

| Field | Type | Description |
|-------|------|-------------|
| `kind` | `DocKind` | brain or code |
| `owner_id` | `str` | Source file grouping |
| `path` | `str` | File path |
| `title` | `str` | Title |
| `snippet` | `str` | Preview text |
| `uri` | `str` | MCP URI |
| `relevance` | `float` | Combined weighted score |
| `lexical_score` | `float` | Keyword match component |
| `semantic_score` | `float` | Combined TF-IDF + semantic embedding component |
| `freshness` | `str` | Freshness state string |
| `status` | `str` | Note status string |
| `source_precision` | `float` | Confidence weight |
| `last_verified` | `str?` | ISO timestamp |
| `source_files_exist` | `bool` | Source file existence |
| `stale_reasons` | `list[str]` | Reasons for staleness |
| `note_type` | `str?` | Note type |
| `line_start` | `int?` | Chunk line start |
| `line_end` | `int?` | Chunk line end |
| `source_of_truth` | `str?` | Set by reconcile: `"brain"`, `"code"`, or `"brain+code"` |
| `contradictions` | `list[str]` | Contradiction messages (populated by reconcile) |
| `metadata` | `dict[str, Any]` | Full metadata dict |

---

## Enumerations

### DocKind
- `brain` -- Notes from the Obsidian vault
- `code` -- Source code chunks from the codebase

### NoteStatus
- `active` -- Current and trusted
- `stale` -- Past decay window, needs review
- `labile` -- Contradictions detected, undergoing reconsolidation
- `superseded` -- Replaced by another note
- `archived` -- No longer relevant

### FreshnessState
- `immutable` -- ADRs and notes with `decay_class=immutable`; never decay
- `current` -- Within first half of decay window
- `aging` -- Past 50% of decay window but not yet stale
- `stale` -- Past decay window entirely
- `missing_sources` -- Linked source files do not exist on disk

### Mode
- `phasic` -- Normal, incremental code changes
- `tonic` -- High volatility (>= `phasic_change_threshold` files changed)

---

## SQLite Schema

Single table in `documents.sqlite3` (defined in `storage.py`):

```sql
CREATE TABLE IF NOT EXISTS documents (
    doc_id       TEXT PRIMARY KEY,
    kind         TEXT NOT NULL,        -- 'brain' | 'code'
    owner_id     TEXT NOT NULL,        -- groups chunks from same file
    path         TEXT NOT NULL,        -- absolute file path
    uri          TEXT NOT NULL,        -- MCP-style URI
    title        TEXT NOT NULL,
    content      TEXT NOT NULL,        -- full chunk text
    snippet      TEXT NOT NULL,        -- preview
    line_start   INTEGER NOT NULL,
    line_end     INTEGER NOT NULL,
    content_hash TEXT NOT NULL,
    metadata_json TEXT NOT NULL        -- JSON blob with freshness, tags, etc.
);

CREATE INDEX IF NOT EXISTS idx_documents_kind ON documents(kind);
CREATE INDEX IF NOT EXISTS idx_documents_owner_id ON documents(owner_id);
CREATE INDEX IF NOT EXISTS idx_documents_path ON documents(path);
```

Operations:
- `replace_kind(kind, docs)`: DELETE all rows for kind, then INSERT new batch (full replace on each index)
- `all_documents(kind?)`: SELECT all rows, optionally filtered by kind

---

## YAML Frontmatter Schema

Brain notes use YAML frontmatter between `---` delimiters. Parsed by `frontmatter.py`.

```yaml
---
title: "Note Title"
type: note            # note_type: note, adr, architecture-doc, tech, component,
                      #            api-doc, bug, bug-fix, workflow, inbox
status: active        # NoteStatus value
tags: [python, mcp]
decay_class: 30d      # immutable, 90d, 60d, 30d, 14d, 7d
source_precision: 0.8 # 0.0-1.0
last_verified: 2026-04-01
created: 2026-03-15
linked_paths:         # source files this note describes
  - src/neuro_mcp/service.py
claimed_dependencies: # packages the note claims are used
  - pydantic
  - scikit-learn
linked_commits:
  - abc1234
superseded_by: null   # path to replacement note
---

Note body content here...
```

---

## Decay Class Defaults by Note Type

| Note Type | Default Decay Class |
|-----------|-------------------|
| `adr` | `immutable` |
| `architecture-doc` / `architecture` | `90d` |
| `tech` | `60d` |
| `component` / `api-doc` / `workflow` / `note` | `30d` |
| `bug` / `bug-fix` | `14d` |
| `inbox` | `7d` |

---

## Report Models

### ReconcileReport
- `query`, `source_of_truth` (`"code"` or `"brain+code"`), `mode`, `brain_results`, `code_results`, `contradictions`, `recommendations`

### DigestReport
- `generated_at`, `mode`, `total_notes`, `stale_notes`, `labile_notes`, `missing_source_notes`, `top_risks`, `next_actions`

### GarbageCollectionReport
- `dry_run`, `mode`, `items` (list of `GarbageCollectionItem`), `total_notes`, `stale_count`, `missing_sources_count`, `archived_candidates`

### GarbageCollectionItem
- `note_id`, `path`, `action` (`keep`/`archive_candidate`/`update_status`), `reason`, `status_before`, `status_after`

### ChangeSet
- `changed_paths`, `recent_commits`, `mode`

---

## Proposed v2 Additions

The following tables are planned for v2 but not yet implemented. They are described here to guide future design.

### reconsolidation_tx (proposed)

Tracks reconsolidation review transactions -- the approve/reject cycle when contradictions are found.

| Column | Type | Description |
|--------|------|-------------|
| `tx_id` | `TEXT PK` | Transaction UUID |
| `note_path` | `TEXT` | Path to the note under review |
| `opened_at` | `TEXT` | ISO timestamp when contradictions triggered the transaction |
| `closed_at` | `TEXT?` | ISO timestamp when resolved |
| `status` | `TEXT` | `open`, `approved`, `rejected`, `expired` |
| `contradictions_json` | `TEXT` | JSON array of contradiction strings |
| `verdict` | `TEXT?` | `accept_brain`, `accept_code`, `merge`, `supersede` |
| `reviewer` | `TEXT?` | Who resolved the transaction |
| `patch_json` | `TEXT?` | Proposed content patch (if any) |

### evidence_edge (proposed)

Explicit edges in a precision-weighted evidence graph, replacing the implicit `linked_paths` + `claimed_dependencies` approach.

| Column | Type | Description |
|--------|------|-------------|
| `edge_id` | `TEXT PK` | Edge UUID |
| `source_doc_id` | `TEXT FK` | DocumentRecord that makes a claim |
| `target_doc_id` | `TEXT FK` | DocumentRecord that provides evidence |
| `edge_type` | `TEXT` | `supports`, `contradicts`, `supersedes`, `depends_on` |
| `weight` | `REAL` | Confidence weight (0.0-1.0) |
| `created_at` | `TEXT` | ISO timestamp |
| `evidence_snippet` | `TEXT?` | Relevant excerpt |

### promotion_log (proposed)

Audit trail for synaptic-tagging promotions (inbox -> permanent note).

| Column | Type | Description |
|--------|------|-------------|
| `log_id` | `TEXT PK` | Log entry UUID |
| `note_id` | `TEXT` | Note that was promoted |
| `old_decay_class` | `TEXT` | e.g., `7d` |
| `new_decay_class` | `TEXT` | e.g., `30d` |
| `reason` | `TEXT` | Why promoted (correlated code changes) |
| `promoted_at` | `TEXT` | ISO timestamp |
| `correlated_files` | `TEXT` | JSON array of file paths that triggered promotion |

## Traceability

- [[1-spec/requirements/REQ-F-reconsolidation-transactions|REQ-F-reconsolidation-transactions]]
- [[1-spec/requirements/REQ-F-evidence-graph-schema|REQ-F-evidence-graph-schema]]
- [[1-spec/requirements/REQ-F-decay-defaults-consistency|REQ-F-decay-defaults-consistency]]
