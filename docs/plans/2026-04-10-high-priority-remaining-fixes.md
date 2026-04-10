# High-Priority Remaining Fixes — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix the 4 remaining high-priority issues from code review: SecretStr for bearer_token, zip strict mode, interference O(n²) cap, SQLite connection reuse.

**Architecture:** Targeted fixes only — each task patches one issue with a test proving the fix. All backward-compatible. 6 of the original 10 high-priority items were already fixed in the previous security batch.

**Tech Stack:** Python 3.10+, pytest, pydantic (SecretStr), sqlite3, numpy

**Project root:** `/Users/benjaminpoersch/Obsidian_new/neuro_mcp/neuro_mcp_server_clean`

---

### Task 1: SecretStr for Bearer Token — `config.py` + `server.py` + `cli.py`

**Files:**
- Modify: `src/neuro_mcp/config.py:7,61`
- Modify: `src/neuro_mcp/server.py:140,145,186`
- Modify: `src/neuro_mcp/cli.py:21,25-26`
- Create: `tests/test_bearer_token_secret.py`

**Step 1: Write the failing test**

```python
# tests/test_bearer_token_secret.py
"""Test that bearer_token uses SecretStr and doesn't leak in repr/str."""
from __future__ import annotations

from pydantic import SecretStr
from neuro_mcp.config import Settings


def test_bearer_token_is_secret_str():
    s = Settings(brain_root="/tmp/b", code_root="/tmp/c", bearer_token="super-secret-123")
    assert isinstance(s.bearer_token, SecretStr)


def test_bearer_token_hidden_in_repr():
    s = Settings(brain_root="/tmp/b", code_root="/tmp/c", bearer_token="super-secret-123")
    text = repr(s)
    assert "super-secret-123" not in text


def test_bearer_token_get_secret_value():
    s = Settings(brain_root="/tmp/b", code_root="/tmp/c", bearer_token="super-secret-123")
    assert s.bearer_token.get_secret_value() == "super-secret-123"


def test_bearer_token_none_by_default():
    s = Settings(brain_root="/tmp/b", code_root="/tmp/c")
    assert s.bearer_token is None
```

**Step 2: Run test to verify it fails**

Run: `cd /sessions/lucid-clever-tesla/mnt/neuro_mcp/neuro_mcp_server_clean && python -m pytest tests/test_bearer_token_secret.py -v --tb=short`
Expected: FAIL (bearer_token is still plain `str`)

**Step 3: Write minimal implementation**

**3a. `src/neuro_mcp/config.py`**

Update pydantic import on line 7. Replace:
```python
from pydantic import BaseModel, Field, field_validator, model_validator
```
With:
```python
from pydantic import BaseModel, Field, SecretStr, field_validator, model_validator
```

Replace line 61:
```python
    bearer_token: str | None = None
```
With:
```python
    bearer_token: SecretStr | None = None
```

**3b. `src/neuro_mcp/server.py`**

Replace line 140:
```python
            if not settings.bearer_token:
```
With:
```python
            if settings.bearer_token is None:
```

Replace line 145:
```python
            expected = f"Bearer {settings.bearer_token}"
```
With:
```python
            expected = f"Bearer {settings.bearer_token.get_secret_value()}"
```

Replace line 186:
```python
    if settings.bearer_token:
```
With:
```python
    if settings.bearer_token is not None:
```

**3c. `src/neuro_mcp/cli.py`**

Replace lines 25-26:
```python
    if args.bearer_token:
        settings.bearer_token = args.bearer_token
```
With:
```python
    if args.bearer_token:
        settings.bearer_token = SecretStr(args.bearer_token)
```

And add import at the top of `cli.py` (after existing imports):
```python
from pydantic import SecretStr
```

**Step 4: Run test to verify it passes**

Run: `cd /sessions/lucid-clever-tesla/mnt/neuro_mcp/neuro_mcp_server_clean && python -m pytest tests/test_bearer_token_secret.py -v --tb=short`
Expected: 4 PASS

**Step 5: Run full suite**

Run: `cd /sessions/lucid-clever-tesla/mnt/neuro_mcp/neuro_mcp_server_clean && python -m pytest tests/ -v --tb=short`
Expected: all pass

**Step 6: Commit**

```bash
git add src/neuro_mcp/config.py src/neuro_mcp/server.py src/neuro_mcp/cli.py tests/test_bearer_token_secret.py
git commit -m "fix(security): use pydantic SecretStr for bearer_token to prevent log leaks"
```

---

### Task 2: Zip Strict Mode + Length Guard — `search.py`

**Files:**
- Modify: `src/neuro_mcp/search.py:31,111-112,122-123`
- Create: `tests/test_search_strict.py`

**Step 1: Write the failing test**

```python
# tests/test_search_strict.py
"""Test that search raises on length mismatch between documents and scores."""
from __future__ import annotations

import numpy as np
import pytest

from neuro_mcp.models import DocKind, DocumentRecord
from neuro_mcp.embeddings import TfidfEmbedder
from neuro_mcp.search import rank_documents


def _make_docs(n: int) -> list[DocumentRecord]:
    return [
        DocumentRecord(
            doc_id=f"d{i}",
            kind=DocKind.BRAIN,
            owner_id=f"o{i}",
            path=f"note{i}.md",
            uri=f"file:///note{i}.md",
            title=f"Note {i}",
            content=f"content about topic {i}",
            snippet=f"snippet {i}",
            line_start=0,
            line_end=10,
            content_hash=f"hash{i}",
            metadata={"freshness": "current", "source_precision": 0.5},
        )
        for i in range(n)
    ]


def test_rank_documents_length_mismatch_raises(tmp_path):
    """If embedder produces fewer scores than documents, should raise ValueError."""
    docs = _make_docs(5)
    embedder = TfidfEmbedder(tmp_path / "model.joblib")
    # Fit on only 3 texts so doc_matrix has 3 rows but we pass 5 documents
    embedder.fit(["topic one", "topic two", "topic three"])
    with pytest.raises(ValueError, match="[Mm]ismatch"):
        rank_documents(
            "topic",
            docs,
            embedder,
            top_k=5,
            semantic_weight=0.55,
            lexical_weight=0.20,
            freshness_weight=0.15,
            precision_weight=0.10,
        )


def test_rank_documents_matching_length_works(tmp_path):
    """Normal case: same number of docs and scores."""
    docs = _make_docs(3)
    embedder = TfidfEmbedder(tmp_path / "model.joblib")
    embedder.fit([d.content for d in docs])
    results = rank_documents(
        "topic",
        docs,
        embedder,
        top_k=3,
        semantic_weight=0.55,
        lexical_weight=0.20,
        freshness_weight=0.15,
        precision_weight=0.10,
    )
    assert len(results) == 3
```

**Step 2: Run test to verify it fails**

Run: `cd /sessions/lucid-clever-tesla/mnt/neuro_mcp/neuro_mcp_server_clean && python -m pytest tests/test_search_strict.py -v --tb=short`
Expected: first test FAIL (no ValueError raised — zip silently truncates)

**Step 3: Write minimal implementation**

In `src/neuro_mcp/search.py`:

Replace line 31:
```python
    for document, semantic in zip(documents, semantic_scores, strict=False):
```
With:
```python
    if len(semantic_scores) != len(documents):
        raise ValueError(
            f"Score/document length mismatch: {len(semantic_scores)} scores vs {len(documents)} documents"
        )
    for document, semantic in zip(documents, semantic_scores, strict=True):
```

Also add a length guard in `rank_documents_hybrid` after line 112. Replace lines 110-112:
```python
    tfidf_scores, semantic_scores = hybrid_embedder.score(query)
    if len(tfidf_scores) == 0 and len(semantic_scores) == 0:
        return []
```
With:
```python
    tfidf_scores, semantic_scores = hybrid_embedder.score(query)
    if len(tfidf_scores) == 0 and len(semantic_scores) == 0:
        return []
    if len(tfidf_scores) > 0 and len(tfidf_scores) != len(documents):
        raise ValueError(
            f"TF-IDF score/document length mismatch: {len(tfidf_scores)} scores vs {len(documents)} documents"
        )
```

**Step 4: Run test to verify it passes**

Run: `cd /sessions/lucid-clever-tesla/mnt/neuro_mcp/neuro_mcp_server_clean && python -m pytest tests/test_search_strict.py -v --tb=short`
Expected: 2 PASS

**Step 5: Run full suite**

Run: `cd /sessions/lucid-clever-tesla/mnt/neuro_mcp/neuro_mcp_server_clean && python -m pytest tests/ -v --tb=short`
Expected: all pass

**Step 6: Commit**

```bash
git add src/neuro_mcp/search.py tests/test_search_strict.py
git commit -m "fix(correctness): enforce strict length matching between documents and scores"
```

---

### Task 3: Interference O(n²) Cap — `interference.py`

**Files:**
- Modify: `src/neuro_mcp/interference.py:18-31,40-42`
- Create: `tests/test_interference_cap.py`

**Step 1: Write the failing test**

```python
# tests/test_interference_cap.py
"""Test that interference check respects max_documents cap."""
from __future__ import annotations

import logging
import numpy as np
import pytest

from neuro_mcp.interference import check_interference


def test_interference_respects_max_documents_cap():
    """If more than max_documents, should raise or truncate with warning."""
    n = 120
    embeddings = np.random.randn(n, 64).astype(np.float32)
    paths = [f"note_{i}.md" for i in range(n)]
    owner_ids = [f"owner_{i}" for i in range(n)]

    # With cap=100, should log a warning and only process first 100
    candidates = check_interference(
        embeddings, paths, owner_ids, threshold=0.99, max_documents=100
    )
    # Should not crash, and should have processed only 100 docs
    assert isinstance(candidates, list)


def test_interference_default_cap_allows_normal_usage():
    """Normal usage with <1000 docs should work without issues."""
    n = 10
    # Create embeddings where first two are nearly identical
    embeddings = np.random.randn(n, 64).astype(np.float32)
    embeddings[1] = embeddings[0] + 0.001  # nearly identical
    paths = [f"note_{i}.md" for i in range(n)]
    owner_ids = [f"owner_{i}" for i in range(n)]

    candidates = check_interference(embeddings, paths, owner_ids, threshold=0.9)
    assert len(candidates) >= 1
    assert candidates[0].note_a_path == "note_0.md"
    assert candidates[0].note_b_path == "note_1.md"


def test_interference_logs_warning_on_cap(caplog):
    """Should log warning when document count exceeds cap."""
    n = 50
    embeddings = np.random.randn(n, 64).astype(np.float32)
    paths = [f"note_{i}.md" for i in range(n)]
    owner_ids = [f"owner_{i}" for i in range(n)]

    with caplog.at_level(logging.WARNING, logger="neuro_mcp.interference"):
        check_interference(embeddings, paths, owner_ids, threshold=0.99, max_documents=20)
    assert any("capped" in r.message.lower() or "truncat" in r.message.lower() for r in caplog.records)
```

**Step 2: Run test to verify it fails**

Run: `cd /sessions/lucid-clever-tesla/mnt/neuro_mcp/neuro_mcp_server_clean && python -m pytest tests/test_interference_cap.py -v --tb=short`
Expected: FAIL (no max_documents parameter)

**Step 3: Write minimal implementation**

Replace the entire `src/neuro_mcp/interference.py` content with:

```python
"""Interference detection: find overlapping/contradicting notes via embedding similarity."""
from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class InterferenceCandidate:
    note_a_path: str
    note_b_path: str
    similarity: float
    action: str   # "merge" | "cross_link" | "supersede"
    reason: str


def check_interference(
    embeddings: np.ndarray,
    paths: list[str],
    owner_ids: list[str],
    threshold: float = 0.85,
    max_documents: int = 1000,
) -> list[InterferenceCandidate]:
    """Pairwise cosine similarity check. Returns candidates above threshold.

    - Same owner_id -> merge candidate (sections of same note are near-duplicates)
    - Different owner_id -> cross_link candidate (different notes overlap)

    If more than *max_documents* are provided, the input is truncated and a
    warning is logged. This prevents O(n^2) blowup on large note bases.
    """
    n = len(paths)
    if n < 2 or embeddings.shape[0] < 2:
        return []

    if n > max_documents:
        logger.warning(
            "Interference check capped: %d documents truncated to %d (O(n^2) safety limit)",
            n,
            max_documents,
        )
        embeddings = embeddings[:max_documents]
        paths = paths[:max_documents]
        owner_ids = owner_ids[:max_documents]
        n = max_documents

    # Normalize if not already
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1.0, norms)
    normed = embeddings / norms

    sim_matrix = normed @ normed.T

    candidates: list[InterferenceCandidate] = []
    for i in range(n):
        for j in range(i + 1, n):
            score = float(sim_matrix[i, j])
            if score >= threshold:
                if owner_ids[i] == owner_ids[j]:
                    action = "merge"
                    reason = f"Same note sections overlap (cosine={score:.3f})"
                else:
                    action = "cross_link"
                    reason = f"Different notes overlap (cosine={score:.3f})"
                candidates.append(InterferenceCandidate(
                    note_a_path=paths[i],
                    note_b_path=paths[j],
                    similarity=score,
                    action=action,
                    reason=reason,
                ))
    candidates.sort(key=lambda c: c.similarity, reverse=True)
    return candidates
```

**Step 4: Run test to verify it passes**

Run: `cd /sessions/lucid-clever-tesla/mnt/neuro_mcp/neuro_mcp_server_clean && python -m pytest tests/test_interference_cap.py -v --tb=short`
Expected: 3 PASS

**Step 5: Run full suite**

Run: `cd /sessions/lucid-clever-tesla/mnt/neuro_mcp/neuro_mcp_server_clean && python -m pytest tests/ -v --tb=short`
Expected: all pass

**Step 6: Commit**

```bash
git add src/neuro_mcp/interference.py tests/test_interference_cap.py
git commit -m "fix(performance): add max_documents cap to interference O(n^2) check"
```

---

### Task 4: SQLite Connection Reuse — `storage.py`

**Files:**
- Modify: `src/neuro_mcp/storage.py:32-41,43-45,47-49,77-78`
- Create: `tests/test_storage_connection.py`

**Step 1: Write the failing test**

```python
# tests/test_storage_connection.py
"""Test that Repository reuses its SQLite connection."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from neuro_mcp.models import DocKind, DocumentRecord
from neuro_mcp.storage import Repository


def test_repository_reuses_connection(tmp_path: Path):
    """Multiple operations should reuse the same connection object."""
    repo = Repository(tmp_path / "test.db")
    conn1 = repo._conn
    repo.all_documents()
    conn2 = repo._conn
    assert conn1 is conn2, "Connection should be reused, not recreated"


def test_repository_close_releases_connection(tmp_path: Path):
    """After close(), connection should be None."""
    repo = Repository(tmp_path / "test.db")
    assert repo._conn is not None
    repo.close()
    assert repo._conn is None


def test_repository_operations_after_close(tmp_path: Path):
    """Operations after close() should auto-reconnect."""
    repo = Repository(tmp_path / "test.db")
    repo.close()
    # Should work — auto-reconnects
    docs = repo.all_documents()
    assert isinstance(docs, list)
    assert repo._conn is not None
```

**Step 2: Run test to verify it fails**

Run: `cd /sessions/lucid-clever-tesla/mnt/neuro_mcp/neuro_mcp_server_clean && python -m pytest tests/test_storage_connection.py -v --tb=short`
Expected: FAIL (no `_conn` attribute or `close()` method)

**Step 3: Write minimal implementation**

Replace the full content of `src/neuro_mcp/storage.py` with:

```python
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Iterable

from .models import DocKind, DocumentRecord


SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    doc_id TEXT PRIMARY KEY,
    kind TEXT NOT NULL,
    owner_id TEXT NOT NULL,
    path TEXT NOT NULL,
    uri TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    snippet TEXT NOT NULL,
    line_start INTEGER NOT NULL,
    line_end INTEGER NOT NULL,
    content_hash TEXT NOT NULL,
    metadata_json TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_documents_kind ON documents(kind);
CREATE INDEX IF NOT EXISTS idx_documents_owner_id ON documents(owner_id);
CREATE INDEX IF NOT EXISTS idx_documents_path ON documents(path);
"""


class Repository:
    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: sqlite3.Connection | None = None
        self._init()

    def _get_conn(self) -> sqlite3.Connection:
        """Return the cached connection, creating it if needed."""
        if self._conn is None:
            self._conn = sqlite3.connect(str(self.db_path))
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def close(self) -> None:
        """Close the cached connection."""
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def _init(self) -> None:
        conn = self._get_conn()
        conn.executescript(SCHEMA)
        conn.commit()

    def replace_kind(self, kind: DocKind, documents: Iterable[DocumentRecord]) -> None:
        docs = list(documents)
        conn = self._get_conn()
        conn.execute("DELETE FROM documents WHERE kind = ?", (kind.value,))
        conn.executemany(
            """
            INSERT INTO documents (
                doc_id, kind, owner_id, path, uri, title, content, snippet,
                line_start, line_end, content_hash, metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    doc.doc_id,
                    doc.kind.value,
                    doc.owner_id,
                    doc.path,
                    doc.uri,
                    doc.title,
                    doc.content,
                    doc.snippet,
                    doc.line_start,
                    doc.line_end,
                    doc.content_hash,
                    json.dumps(doc.metadata, ensure_ascii=True),
                )
                for doc in docs
            ],
        )
        conn.commit()

    def all_documents(self, kind: DocKind | None = None) -> list[DocumentRecord]:
        conn = self._get_conn()
        if kind is None:
            rows = conn.execute("SELECT * FROM documents ORDER BY kind, path, line_start").fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM documents WHERE kind = ? ORDER BY path, line_start",
                (kind.value,),
            ).fetchall()
        return [self._row_to_document(row) for row in rows]

    @staticmethod
    def _row_to_document(row: sqlite3.Row) -> DocumentRecord:
        return DocumentRecord(
            doc_id=row["doc_id"],
            kind=DocKind(row["kind"]),
            owner_id=row["owner_id"],
            path=row["path"],
            uri=row["uri"],
            title=row["title"],
            content=row["content"],
            snippet=row["snippet"],
            line_start=row["line_start"],
            line_end=row["line_end"],
            content_hash=row["content_hash"],
            metadata=json.loads(row["metadata_json"]),
        )
```

**Step 4: Run test to verify it passes**

Run: `cd /sessions/lucid-clever-tesla/mnt/neuro_mcp/neuro_mcp_server_clean && python -m pytest tests/test_storage_connection.py -v --tb=short`
Expected: 3 PASS

**Step 5: Run full suite**

Run: `cd /sessions/lucid-clever-tesla/mnt/neuro_mcp/neuro_mcp_server_clean && python -m pytest tests/ -v --tb=short`
Expected: all pass

**Step 6: Commit**

```bash
git add src/neuro_mcp/storage.py tests/test_storage_connection.py
git commit -m "fix(performance): reuse SQLite connection instead of creating per query"
```

---

### Task 5: End-to-End Verification + Push

**Step 1: Run full test suite**

Run: `cd /sessions/lucid-clever-tesla/mnt/neuro_mcp/neuro_mcp_server_clean && python -m pytest tests/ -v --tb=short`
Expected: all pass (~60+ tests now)

**Step 2: py_compile all modified modules**

Run:
```bash
cd /sessions/lucid-clever-tesla/mnt/neuro_mcp/neuro_mcp_server_clean
python -m py_compile src/neuro_mcp/config.py
python -m py_compile src/neuro_mcp/server.py
python -m py_compile src/neuro_mcp/cli.py
python -m py_compile src/neuro_mcp/search.py
python -m py_compile src/neuro_mcp/interference.py
python -m py_compile src/neuro_mcp/storage.py
```
Expected: no errors

**Step 3: Verify MCP tool count unchanged**

Run:
```bash
cd /sessions/lucid-clever-tesla/mnt/neuro_mcp/neuro_mcp_server_clean
python -c "
from neuro_mcp.config import Settings
from neuro_mcp.server import create_mcp_app
s = Settings(brain_root='/tmp/b', code_root='/tmp/c')
app = create_mcp_app(s)
tools = app._tool_manager.list_tools()
print(f'Tools: {len(tools)}')
assert len(tools) == 10
print('OK')
"
```
Expected: `Tools: 10` then `OK`

**Step 4: Push**

```bash
git push origin main
```
