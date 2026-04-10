# Critical Security & Correctness Fixes — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix the 5 critical security vulnerabilities and 5 high-priority correctness bugs found in code review.

**Architecture:** Targeted fixes only — no refactors, no new features. Each task patches one vulnerability with a test proving the fix. All fixes are backward-compatible.

**Tech Stack:** Python 3.10+, pytest, pydantic, hmac, hashlib, pathlib

**Project root:** `/Users/benjaminpoersch/Obsidian_new/neuro_mcp/neuro_mcp_server_clean`

---

### Task 1: Path Traversal Guard — `writer.py`

**Files:**
- Modify: `src/neuro_mcp/writer.py:28-29`
- Create: `tests/test_writer_security.py`

**Step 1: Write the failing test**

```python
# tests/test_writer_security.py
"""Security tests for writer module."""
from __future__ import annotations

import pytest
from pathlib import Path
from neuro_mcp.writer import write_note


def test_write_note_rejects_path_traversal(tmp_path: Path):
    brain_root = tmp_path / "brain"
    brain_root.mkdir()
    with pytest.raises(ValueError, match="outside brain root"):
        write_note(brain_root, "../../../etc/evil.md", title="hack", content="pwned")


def test_write_note_rejects_absolute_path(tmp_path: Path):
    brain_root = tmp_path / "brain"
    brain_root.mkdir()
    with pytest.raises(ValueError, match="outside brain root"):
        write_note(brain_root, "/etc/passwd", title="hack", content="pwned")


def test_write_note_allows_valid_subpath(tmp_path: Path):
    brain_root = tmp_path / "brain"
    brain_root.mkdir()
    result = write_note(brain_root, "notes/valid.md", title="ok", content="fine")
    assert result["status"] == "created"
    assert (brain_root / "notes" / "valid.md").exists()
```

**Step 2: Run test to verify it fails**

Run: `cd /sessions/lucid-clever-tesla/mnt/neuro_mcp/neuro_mcp_server_clean && python -m pytest tests/test_writer_security.py -v --tb=short`
Expected: 2 FAIL (no ValueError raised), 1 PASS

**Step 3: Write minimal implementation**

Add path validation after line 28 in `src/neuro_mcp/writer.py`. Replace lines 28-29:

```python
    """Write or update a note. Returns status dict."""
    full_path = brain_root / relative_path
    existed = full_path.exists()
```

With:

```python
    """Write or update a note. Returns status dict."""
    full_path = (brain_root / relative_path).resolve()
    if not full_path.is_relative_to(brain_root.resolve()):
        raise ValueError(f"Path escapes outside brain root: {relative_path}")
    existed = full_path.exists()
```

**Step 4: Run test to verify it passes**

Run: `cd /sessions/lucid-clever-tesla/mnt/neuro_mcp/neuro_mcp_server_clean && python -m pytest tests/test_writer_security.py -v --tb=short`
Expected: 3 PASS

**Step 5: Run full suite to check no regressions**

Run: `cd /sessions/lucid-clever-tesla/mnt/neuro_mcp/neuro_mcp_server_clean && python -m pytest tests/ -v --tb=short`
Expected: all pass

**Step 6: Commit**

```bash
git add tests/test_writer_security.py src/neuro_mcp/writer.py
git commit -m "fix(security): prevent path traversal in writer.write_note"
```

---

### Task 2: Path Traversal Guard — `service.py` (get_note)

**Files:**
- Modify: `src/neuro_mcp/service.py:178-182`
- Create: `tests/test_get_note_security.py`

**Step 1: Write the failing test**

```python
# tests/test_get_note_security.py
"""Security tests for get_note path handling."""
from __future__ import annotations

from pathlib import Path
from neuro_mcp.config import Settings
from neuro_mcp.service import NeuroMCPService


def test_get_note_rejects_path_traversal(tmp_path: Path):
    brain = tmp_path / "brain"
    brain.mkdir()
    code = tmp_path / "code"
    code.mkdir()
    settings = Settings(brain_root=brain, code_root=code, data_dir=tmp_path / "data")
    svc = NeuroMCPService(settings)
    result = svc.get_note("../../../etc/passwd")
    assert result["found"] is False
    assert "traversal" in result.get("error", "").lower() or "outside" in result.get("error", "").lower()


def test_get_note_allows_valid_path(tmp_path: Path):
    brain = tmp_path / "brain"
    brain.mkdir()
    code = tmp_path / "code"
    code.mkdir()
    note = brain / "test.md"
    note.write_text("---\ntitle: test\n---\nhello", encoding="utf-8")
    settings = Settings(brain_root=brain, code_root=code, data_dir=tmp_path / "data")
    svc = NeuroMCPService(settings)
    result = svc.get_note("test.md")
    assert result["found"] is True
```

**Step 2: Run test to verify it fails**

Run: `cd /sessions/lucid-clever-tesla/mnt/neuro_mcp/neuro_mcp_server_clean && python -m pytest tests/test_get_note_security.py -v --tb=short`
Expected: first test FAIL (returns file-not-found instead of traversal error)

**Step 3: Write minimal implementation**

In `src/neuro_mcp/service.py`, replace lines 178-182:

```python
    def get_note(self, relative_path: str) -> dict:
        """Retrieve a specific brain note by relative path."""
        full_path = self.settings.brain_root / relative_path
        if not full_path.exists() or not full_path.is_file():
            return {"found": False, "path": relative_path, "error": "Note not found"}
```

With:

```python
    def get_note(self, relative_path: str) -> dict:
        """Retrieve a specific brain note by relative path."""
        full_path = (self.settings.brain_root / relative_path).resolve()
        if not full_path.is_relative_to(self.settings.brain_root.resolve()):
            return {"found": False, "path": relative_path, "error": "Path traversal outside brain root"}
        if not full_path.exists() or not full_path.is_file():
            return {"found": False, "path": relative_path, "error": "Note not found"}
```

**Step 4: Run test to verify it passes**

Run: `cd /sessions/lucid-clever-tesla/mnt/neuro_mcp/neuro_mcp_server_clean && python -m pytest tests/test_get_note_security.py -v --tb=short`
Expected: 2 PASS

**Step 5: Run full suite**

Run: `cd /sessions/lucid-clever-tesla/mnt/neuro_mcp/neuro_mcp_server_clean && python -m pytest tests/ -v --tb=short`
Expected: all pass

**Step 6: Commit**

```bash
git add tests/test_get_note_security.py src/neuro_mcp/service.py
git commit -m "fix(security): prevent path traversal in service.get_note"
```

---

### Task 3: Bearer Token Timing Attack — `server.py`

**Files:**
- Modify: `src/neuro_mcp/server.py:143-145`

**Step 1: Write minimal implementation**

In `src/neuro_mcp/server.py`, add import at the top of the file (after the existing `from __future__` import):

```python
import hmac
```

Then replace line 145:

```python
            if token == expected:
```

With:

```python
            if hmac.compare_digest(token, expected):
```

**Step 2: Run full suite to check no regressions**

Run: `cd /sessions/lucid-clever-tesla/mnt/neuro_mcp/neuro_mcp_server_clean && python -m pytest tests/ -v --tb=short`
Expected: all pass

**Step 3: Commit**

```bash
git add src/neuro_mcp/server.py
git commit -m "fix(security): use constant-time comparison for bearer token"
```

---

### Task 4: Symlink Safety — `notes.py` and `codebase.py`

**Files:**
- Modify: `src/neuro_mcp/notes.py:96`
- Modify: `src/neuro_mcp/codebase.py:25-33`
- Create: `tests/test_symlink_safety.py`

**Step 1: Write the failing test**

```python
# tests/test_symlink_safety.py
"""Test that scanning ignores symlinks pointing outside root."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from neuro_mcp.config import Settings
from neuro_mcp.notes import scan_brain_documents
from neuro_mcp.codebase import scan_code_documents


@pytest.fixture
def symlink_env(tmp_path: Path):
    brain = tmp_path / "brain"
    brain.mkdir()
    code = tmp_path / "code"
    code.mkdir()
    outside = tmp_path / "secret"
    outside.mkdir()
    (outside / "leak.md").write_text("---\ntitle: secret\n---\ntop secret data")

    # Create symlink from brain -> outside
    symlink = brain / "evil_link"
    try:
        symlink.symlink_to(outside)
    except OSError:
        pytest.skip("Cannot create symlinks on this OS")

    settings = Settings(brain_root=brain, code_root=code, data_dir=tmp_path / "data")
    return settings, outside


def test_brain_scan_ignores_symlinked_dirs(symlink_env):
    settings, outside = symlink_env
    documents, notes = scan_brain_documents(settings)
    paths = [d.path for d in documents]
    assert not any("leak" in p for p in paths), f"Symlink leak found in: {paths}"


def test_code_scan_ignores_symlinked_dirs(symlink_env):
    settings, outside = symlink_env
    # Put a .py file in the secret dir
    (outside / "evil.py").write_text("print('hacked')")
    documents, manifests = scan_code_documents(settings)
    paths = [d.path for d in documents]
    assert not any("evil" in p for p in paths), f"Symlink leak found in: {paths}"
```

**Step 2: Run test to verify it fails**

Run: `cd /sessions/lucid-clever-tesla/mnt/neuro_mcp/neuro_mcp_server_clean && python -m pytest tests/test_symlink_safety.py -v --tb=short`
Expected: FAIL (symlinked files are found)

**Step 3: Write minimal implementation**

In `src/neuro_mcp/notes.py`, replace line 96:

```python
    for path in sorted(root.rglob("*.md")):
```

With:

```python
    for path in sorted(root.rglob("*.md")):
        if path.resolve().is_relative_to(root.resolve()) is False:
            continue
```

In `src/neuro_mcp/codebase.py`, after line 27 (`continue` after `is_dir()`), add:

```python
        if not path.resolve().is_relative_to(root.resolve()):
            continue
```

So lines 25-29 become:

```python
    for path in sorted(root.rglob("*")):
        if path.is_dir():
            continue
        if not path.resolve().is_relative_to(root.resolve()):
            continue
        if path_is_excluded(path, settings.exclude_dirs):
```

**Step 4: Run test to verify it passes**

Run: `cd /sessions/lucid-clever-tesla/mnt/neuro_mcp/neuro_mcp_server_clean && python -m pytest tests/test_symlink_safety.py -v --tb=short`
Expected: 2 PASS (or 2 SKIP if symlinks not supported)

**Step 5: Run full suite**

Run: `cd /sessions/lucid-clever-tesla/mnt/neuro_mcp/neuro_mcp_server_clean && python -m pytest tests/ -v --tb=short`
Expected: all pass

**Step 6: Commit**

```bash
git add tests/test_symlink_safety.py src/neuro_mcp/notes.py src/neuro_mcp/codebase.py
git commit -m "fix(security): ignore symlinks pointing outside root in brain/code scanning"
```

---

### Task 5: SHA1 → SHA256 for Stable IDs — `text_utils.py`

**Files:**
- Modify: `src/neuro_mcp/text_utils.py:13`

**Step 1: Write minimal implementation**

In `src/neuro_mcp/text_utils.py`, replace line 13:

```python
    digest = hashlib.sha1("||".join(parts).encode("utf-8")).hexdigest()
```

With:

```python
    digest = hashlib.sha256("||".join(parts).encode("utf-8")).hexdigest()
```

**Step 2: Run full suite**

Run: `cd /sessions/lucid-clever-tesla/mnt/neuro_mcp/neuro_mcp_server_clean && python -m pytest tests/ -v --tb=short`
Expected: all pass (IDs change but are only used as opaque keys)

**Step 3: Commit**

```bash
git add src/neuro_mcp/text_utils.py
git commit -m "fix(security): use SHA256 instead of SHA1 for stable IDs"
```

---

### Task 6: GC Backup Collision Fix — `gc.py`

**Files:**
- Modify: `src/neuro_mcp/gc.py:93-95`
- Create: `tests/test_gc_backup_collision.py`

**Step 1: Write the failing test**

```python
# tests/test_gc_backup_collision.py
"""Test that GC backups don't collide for same-named files in different dirs."""
from __future__ import annotations

from pathlib import Path
from neuro_mcp.models import GarbageCollectionItem
from neuro_mcp.gc import execute_gc_actions


def test_backup_preserves_both_files(tmp_path: Path):
    # Create two notes with same filename in different dirs
    dir_a = tmp_path / "dir_a"
    dir_b = tmp_path / "dir_b"
    dir_a.mkdir()
    dir_b.mkdir()

    note_a = dir_a / "note.md"
    note_b = dir_b / "note.md"
    note_a.write_text("---\ntitle: A\n---\ncontent A")
    note_b.write_text("---\ntitle: B\n---\ncontent B")

    backup_dir = tmp_path / "backups"

    items = [
        GarbageCollectionItem(
            note_id="a", path=str(note_a), status_before="active",
            status_after="archived", action="archive",
        ),
        GarbageCollectionItem(
            note_id="b", path=str(note_b), status_before="active",
            status_after="archived", action="archive",
        ),
    ]

    results = execute_gc_actions(items, backup_dir=backup_dir)
    assert all(r["executed"] for r in results)

    # Both backups must exist and have different content
    backup_files = list(backup_dir.rglob("*.md"))
    assert len(backup_files) >= 2, f"Expected 2 backups, got {len(backup_files)}: {backup_files}"
```

**Step 2: Run test to verify it fails**

Run: `cd /sessions/lucid-clever-tesla/mnt/neuro_mcp/neuro_mcp_server_clean && python -m pytest tests/test_gc_backup_collision.py -v --tb=short`
Expected: FAIL (second backup overwrites first)

**Step 3: Write minimal implementation**

In `src/neuro_mcp/gc.py`, replace lines 93-95:

```python
        if backup_dir:
            backup_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, backup_dir / path.name)
```

With:

```python
        if backup_dir:
            backup_dir.mkdir(parents=True, exist_ok=True)
            backup_name = f"{item.note_id}_{path.name}"
            shutil.copy2(path, backup_dir / backup_name)
```

**Step 4: Run test to verify it passes**

Run: `cd /sessions/lucid-clever-tesla/mnt/neuro_mcp/neuro_mcp_server_clean && python -m pytest tests/test_gc_backup_collision.py -v --tb=short`
Expected: PASS

**Step 5: Run full suite**

Run: `cd /sessions/lucid-clever-tesla/mnt/neuro_mcp/neuro_mcp_server_clean && python -m pytest tests/ -v --tb=short`
Expected: all pass

**Step 6: Commit**

```bash
git add tests/test_gc_backup_collision.py src/neuro_mcp/gc.py
git commit -m "fix: prevent GC backup filename collisions using note_id prefix"
```

---

### Task 7: Watcher Error Resilience — `watcher.py`

**Files:**
- Modify: `src/neuro_mcp/watcher.py:17-19`

**Step 1: Write minimal implementation**

Replace the full content of `src/neuro_mcp/watcher.py`:

```python
"""File system watcher with debounce for auto-reindexing."""
from __future__ import annotations

import asyncio
import logging

from .service import NeuroMCPService

logger = logging.getLogger(__name__)


async def watch_forever(
    service: NeuroMCPService,
    debounce_seconds: float = 5.0,
) -> None:
    """Watch brain and code roots, re-index on changes with debounce."""
    from watchfiles import awatch

    roots = [service.settings.brain_root, service.settings.code_root]
    async for _changes in awatch(*roots, debounce=int(debounce_seconds * 1000)):
        try:
            service.refresh()
        except Exception:
            logger.exception("Error during auto-refresh after file change")
        await asyncio.sleep(0)
```

**Step 2: Run full suite**

Run: `cd /sessions/lucid-clever-tesla/mnt/neuro_mcp/neuro_mcp_server_clean && python -m pytest tests/ -v --tb=short`
Expected: all pass

**Step 3: Commit**

```bash
git add src/neuro_mcp/watcher.py
git commit -m "fix: add error handling in watcher to prevent crash on refresh failure"
```

---

### Task 8: Frontmatter Windows Line Endings — `frontmatter.py`

**Files:**
- Modify: `src/neuro_mcp/frontmatter.py:10`
- Create: `tests/test_frontmatter_crlf.py`

**Step 1: Write the failing test**

```python
# tests/test_frontmatter_crlf.py
"""Test that frontmatter parser handles Windows CRLF line endings."""
from __future__ import annotations

from pathlib import Path
from neuro_mcp.frontmatter import parse_markdown_note


def test_parse_crlf_frontmatter(tmp_path: Path):
    note = tmp_path / "note.md"
    note.write_bytes(b"---\r\ntitle: hello\r\n---\r\n\r\nBody text")
    meta, body = parse_markdown_note(note)
    assert meta.get("title") == "hello"
    assert "Body" in body
```

**Step 2: Run test to verify it fails**

Run: `cd /sessions/lucid-clever-tesla/mnt/neuro_mcp/neuro_mcp_server_clean && python -m pytest tests/test_frontmatter_crlf.py -v --tb=short`
Expected: FAIL (regex doesn't match CRLF)

**Step 3: Write minimal implementation**

In `src/neuro_mcp/frontmatter.py`, replace line 10:

```python
FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.DOTALL)
```

With:

```python
FRONTMATTER_RE = re.compile(r"^---\r?\n(.*?)\r?\n---\r?\n(.*)$", re.DOTALL)
```

**Step 4: Run test to verify it passes**

Run: `cd /sessions/lucid-clever-tesla/mnt/neuro_mcp/neuro_mcp_server_clean && python -m pytest tests/test_frontmatter_crlf.py -v --tb=short`
Expected: PASS

**Step 5: Run full suite**

Run: `cd /sessions/lucid-clever-tesla/mnt/neuro_mcp/neuro_mcp_server_clean && python -m pytest tests/ -v --tb=short`
Expected: all pass

**Step 6: Commit**

```bash
git add tests/test_frontmatter_crlf.py src/neuro_mcp/frontmatter.py
git commit -m "fix: handle CRLF line endings in frontmatter parser"
```

---

### Task 9: Config Weight Validation — `config.py`

**Files:**
- Modify: `src/neuro_mcp/config.py` (add validator after line 74)
- Create: `tests/test_config_validation.py`

**Step 1: Write the failing test**

```python
# tests/test_config_validation.py
"""Test config weight validation."""
from __future__ import annotations

import pytest
from pydantic import ValidationError
from neuro_mcp.config import Settings


def test_search_weights_must_sum_to_one():
    with pytest.raises(ValidationError, match="[Ww]eight"):
        Settings(
            brain_root="/tmp/b",
            code_root="/tmp/c",
            semantic_weight=0.9,
            lexical_weight=0.9,
            freshness_weight=0.9,
            precision_weight=0.9,
        )


def test_hybrid_weights_must_sum_to_one():
    with pytest.raises(ValidationError, match="[Ww]eight"):
        Settings(
            brain_root="/tmp/b",
            code_root="/tmp/c",
            semantic_model_weight=0.8,
            tfidf_model_weight=0.8,
        )


def test_default_weights_are_valid():
    s = Settings(brain_root="/tmp/b", code_root="/tmp/c")
    total = s.semantic_weight + s.lexical_weight + s.freshness_weight + s.precision_weight
    assert abs(total - 1.0) < 0.01
```

**Step 2: Run test to verify it fails**

Run: `cd /sessions/lucid-clever-tesla/mnt/neuro_mcp/neuro_mcp_server_clean && python -m pytest tests/test_config_validation.py -v --tb=short`
Expected: first two FAIL (no validation), third PASS

**Step 3: Write minimal implementation**

In `src/neuro_mcp/config.py`, add after line 74 (before the `_expand` validator), import `model_validator` and add two validators:

First, update the pydantic import on line 6:

```python
from pydantic import BaseModel, Field, field_validator, model_validator
```

Then add after line 74 (before the `@field_validator("brain_root", ...)`):

```python
    @model_validator(mode="after")
    def _check_search_weights(self) -> "Settings":
        total = self.semantic_weight + self.lexical_weight + self.freshness_weight + self.precision_weight
        if abs(total - 1.0) > 0.05:
            raise ValueError(f"Search weights must sum to ~1.0, got {total:.2f}")
        return self

    @model_validator(mode="after")
    def _check_hybrid_weights(self) -> "Settings":
        total = self.semantic_model_weight + self.tfidf_model_weight
        if abs(total - 1.0) > 0.05:
            raise ValueError(f"Hybrid embedding weights must sum to ~1.0, got {total:.2f}")
        return self
```

**Step 4: Run test to verify it passes**

Run: `cd /sessions/lucid-clever-tesla/mnt/neuro_mcp/neuro_mcp_server_clean && python -m pytest tests/test_config_validation.py -v --tb=short`
Expected: 3 PASS

**Step 5: Run full suite**

Run: `cd /sessions/lucid-clever-tesla/mnt/neuro_mcp/neuro_mcp_server_clean && python -m pytest tests/ -v --tb=short`
Expected: all pass

**Step 6: Commit**

```bash
git add tests/test_config_validation.py src/neuro_mcp/config.py
git commit -m "fix: validate search and hybrid embedding weights sum to 1.0"
```

---

### Task 10: Hybrid Embeddings — Silent Fallback Logging

**Files:**
- Modify: `src/neuro_mcp/hybrid_embeddings.py:45-49`

**Step 1: Write minimal implementation**

At the top of `src/neuro_mcp/hybrid_embeddings.py`, after the existing imports, add:

```python
import logging

logger = logging.getLogger(__name__)
```

Then replace lines 45-49:

```python
                try:
                    import sentence_transformers  # noqa: F401
                    self._has_st = True
                except ImportError:
                    self._has_st = False
```

With:

```python
                try:
                    import sentence_transformers  # noqa: F401
                    self._has_st = True
                except ImportError:
                    self._has_st = False
                    logger.warning(
                        "sentence-transformers not installed — falling back to TF-IDF only. "
                        "Install with: pip install 'neuro-mcp-server[semantic]'"
                    )
```

**Step 2: Run full suite**

Run: `cd /sessions/lucid-clever-tesla/mnt/neuro_mcp/neuro_mcp_server_clean && python -m pytest tests/ -v --tb=short`
Expected: all pass

**Step 3: Commit**

```bash
git add src/neuro_mcp/hybrid_embeddings.py
git commit -m "fix: log warning when sentence-transformers not available"
```

---

### Task 11: End-to-End Verification

**Step 1: Run full test suite**

Run: `cd /sessions/lucid-clever-tesla/mnt/neuro_mcp/neuro_mcp_server_clean && python -m pytest tests/ -v --tb=short`
Expected: all pass (should be ~46+ tests now with new security tests)

**Step 2: py_compile all modified modules**

Run:
```bash
cd /sessions/lucid-clever-tesla/mnt/neuro_mcp/neuro_mcp_server_clean
python -m py_compile src/neuro_mcp/writer.py
python -m py_compile src/neuro_mcp/service.py
python -m py_compile src/neuro_mcp/server.py
python -m py_compile src/neuro_mcp/notes.py
python -m py_compile src/neuro_mcp/codebase.py
python -m py_compile src/neuro_mcp/text_utils.py
python -m py_compile src/neuro_mcp/gc.py
python -m py_compile src/neuro_mcp/watcher.py
python -m py_compile src/neuro_mcp/frontmatter.py
python -m py_compile src/neuro_mcp/config.py
python -m py_compile src/neuro_mcp/hybrid_embeddings.py
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
assert len(tools) == 10, f'Expected 10, got {len(tools)}'
print('OK')
"
```
Expected: `Tools: 10` then `OK`

**Step 4: Push fixes**

```bash
git push origin main
```
