# Async, Thread-Safety & Dependency Parsing Fixes — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix the four critical/high bugs not covered by the existing plans: async event-loop blocking in the file watcher, unsafe pickle deserialization of joblib indices, a race condition in `refresh()` under HTTP concurrency, and broken TOML/go.mod dependency extraction.

**Architecture:** Targeted fixes only — no refactors beyond what each bug requires. Each task has a test first (TDD red-green-commit). All changes are backward-compatible; no public API changes.

**Tech Stack:** Python 3.11+, pytest, asyncio, threading, tomllib (stdlib), sqlite3

**Project root:** `/Users/benjaminpoersch/Obsidian_new/neuro_mcp/neuro_mcp_server_clean`

---

### Task 1: Fix async event-loop blocking in `watcher.py`

**Background:** `service.refresh()` does file I/O, SQL writes, and TF-IDF model fitting — all synchronously. It is called from `watch_forever`, which runs inside the Starlette `lifespan` async context. Calling blocking code on the event loop stalls every in-flight HTTP/MCP request until the re-index completes.

**Files:**
- Modify: `src/neuro_mcp/watcher.py`
- Create: `tests/test_watcher_async.py`

**Step 1: Write the failing test**

```python
# tests/test_watcher_async.py
"""Test that watch_forever dispatches refresh to a thread pool, not inline."""
from __future__ import annotations

import asyncio
import threading
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from neuro_mcp.watcher import watch_forever


def test_refresh_runs_in_executor():
    """refresh() must not block the event loop — it must be submitted to an executor."""
    service = MagicMock()
    service.settings.brain_root = "/tmp/brain"
    service.settings.code_root = "/tmp/code"

    calls_on_threads: list[str] = []

    def fake_refresh():
        # Record whether we are on the main thread or a worker thread
        calls_on_threads.append(threading.current_thread().name)

    service.refresh.side_effect = fake_refresh

    async def run_one_cycle():
        # Patch awatch to yield exactly one change then stop
        async def fake_awatch(*roots, **kwargs):
            yield {("modified", "/tmp/brain/note.md")}

        with patch("neuro_mcp.watcher.awatch", new=fake_awatch):
            await watch_forever(service, debounce_seconds=0)

    asyncio.run(run_one_cycle())

    # refresh() must have been called
    service.refresh.assert_called_once()
    # It must NOT have run on the main thread (the event loop thread)
    main_thread_name = threading.main_thread().name
    assert all(
        name != main_thread_name for name in calls_on_threads
    ), f"refresh() ran on main thread: {calls_on_threads}"
```

**Step 2: Run test to verify it fails**

```bash
cd /Users/benjaminpoersch/Obsidian_new/neuro_mcp/neuro_mcp_server_clean
python -m pytest tests/test_watcher_async.py -v --tb=short
```

Expected: FAIL — refresh is called on the main thread.

**Step 3: Write minimal implementation**

Replace the full content of `src/neuro_mcp/watcher.py`:

```python
"""File system watcher with debounce for auto-reindexing."""
from __future__ import annotations

import asyncio
import logging

from watchfiles import awatch

from .service import NeuroMCPService

logger = logging.getLogger(__name__)


async def watch_forever(
    service: NeuroMCPService,
    debounce_seconds: float = 5.0,
) -> None:
    """Watch brain and code roots, re-index on changes with debounce.

    refresh() is CPU- and I/O-heavy (file reads, SQL writes, TF-IDF fit).
    It is dispatched to a thread pool via run_in_executor so the event loop
    stays responsive to MCP/HTTP requests during re-indexing.
    """
    loop = asyncio.get_running_loop()
    roots = [service.settings.brain_root, service.settings.code_root]
    async for _changes in awatch(*roots, debounce=int(debounce_seconds * 1000)):
        try:
            await loop.run_in_executor(None, service.refresh)
        except Exception:
            logger.exception("Error during auto-refresh after file change")
```

**Step 4: Run test to verify it passes**

```bash
cd /Users/benjaminpoersch/Obsidian_new/neuro_mcp/neuro_mcp_server_clean
python -m pytest tests/test_watcher_async.py -v --tb=short
```

Expected: PASS

**Step 5: Run full suite**

```bash
cd /Users/benjaminpoersch/Obsidian_new/neuro_mcp/neuro_mcp_server_clean
python -m pytest tests/ -v --tb=short
```

Expected: all pass

**Step 6: Commit**

```bash
git add src/neuro_mcp/watcher.py tests/test_watcher_async.py
git commit -m "fix(async): run service.refresh() in thread pool to avoid blocking event loop"
```

---

### Task 2: Add thread lock to `service.refresh()` and mutating operations

**Background:** Under `streamable-http` transport, multiple MCP tool calls arrive concurrently. If the file watcher triggers `refresh()` while `search_brain()` iterates over `repo.all_documents()`, the TF-IDF doc matrix and SQLite state are replaced mid-flight. `self._loaded = False` in `ingest_note` compounds this — a search that starts just after the flag is cleared but before `refresh()` completes calls `_ensure_loaded()` → `load()` → `refresh()` a second time concurrently.

**Files:**
- Modify: `src/neuro_mcp/service.py`
- Create: `tests/test_service_thread_safety.py`

**Step 1: Write the failing test**

```python
# tests/test_service_thread_safety.py
"""Test that concurrent refresh() + search() calls don't corrupt state."""
from __future__ import annotations

import threading
import time
from pathlib import Path

import pytest

from neuro_mcp.config import Settings
from neuro_mcp.service import NeuroMCPService


@pytest.fixture
def svc(tmp_path: Path) -> NeuroMCPService:
    brain = tmp_path / "brain"
    brain.mkdir()
    code = tmp_path / "code"
    code.mkdir()
    # Write one note so there's something to index
    (brain / "note.md").write_text(
        "---\ntitle: Test\nlast_verified: 2026-04-10\n---\nContent about testing.",
        encoding="utf-8",
    )
    settings = Settings(brain_root=brain, code_root=code, data_dir=tmp_path / "data")
    return NeuroMCPService(settings)


def test_concurrent_refresh_and_search_do_not_raise(svc: NeuroMCPService):
    """refresh() and search_brain() running concurrently must not raise or deadlock."""
    errors: list[Exception] = []

    def do_refresh():
        for _ in range(5):
            try:
                svc.refresh()
            except Exception as exc:
                errors.append(exc)
            time.sleep(0.01)

    def do_search():
        for _ in range(10):
            try:
                svc.search_brain("testing", top_k=3)
            except Exception as exc:
                errors.append(exc)
            time.sleep(0.005)

    threads = [
        threading.Thread(target=do_refresh),
        threading.Thread(target=do_search),
        threading.Thread(target=do_search),
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=10)

    assert not errors, f"Concurrent errors: {errors}"
```

**Step 2: Run test to verify it fails (or is flaky)**

```bash
cd /Users/benjaminpoersch/Obsidian_new/neuro_mcp/neuro_mcp_server_clean
python -m pytest tests/test_service_thread_safety.py -v --tb=short
```

Expected: may pass intermittently (race conditions are non-deterministic), but run it 3× — it should fail at least once with a numpy/sqlite error or ValueError.

**Step 3: Write minimal implementation**

In `src/neuro_mcp/service.py`, add a `threading` import and a lock. Find the `__init__` method and add the lock after `self._loaded = False`:

```python
# At the top of service.py, add to imports:
import threading
```

In `NeuroMCPService.__init__`, after `self._loaded = False`, add:

```python
        self._refresh_lock = threading.Lock()
```

Wrap `refresh()` with the lock. Replace the current `refresh` method body:

```python
    def refresh(self) -> None:
        with self._refresh_lock:
            brain_docs, notes = scan_brain_documents(self.settings)
            code_docs, manifests = scan_code_documents(self.settings)

            self.repo.replace_kind(DocKind.BRAIN, brain_docs)
            self.repo.replace_kind(DocKind.CODE, code_docs)

            self.brain_hybrid.fit([doc.content for doc in brain_docs])
            self.code_hybrid.fit([doc.content for doc in code_docs])
            self.brain_embedder.save()
            self.code_embedder.save()

            self.notes = notes
            self.manifests = manifests
            self._loaded = True
```

Wrap `_ensure_loaded` to also acquire the lock when calling `load()`:

```python
    def _ensure_loaded(self) -> None:
        if not self._loaded:
            self.load()
```

The `load()` method calls `refresh()` which already holds the lock — this is safe because Python's `threading.Lock` is NOT re-entrant. Change `load()` to directly call `refresh()` (which owns the lock):

```python
    def load(self) -> None:
        # refresh() acquires the lock internally
        self.refresh()
```

> **Note:** If `_ensure_loaded` is called while `refresh()` holds the lock (e.g. from a search thread that started just as the watcher fired `refresh()`), the search thread will block until `refresh()` finishes — which is the correct behavior. Deadlock is impossible because `_ensure_loaded` never holds the lock before calling `load()`.

**Step 4: Run test to verify it passes**

```bash
cd /Users/benjaminpoersch/Obsidian_new/neuro_mcp/neuro_mcp_server_clean
python -m pytest tests/test_service_thread_safety.py -v --tb=short
```

Expected: PASS (run 3× to confirm stability)

**Step 5: Run full suite**

```bash
cd /Users/benjaminpoersch/Obsidian_new/neuro_mcp/neuro_mcp_server_clean
python -m pytest tests/ -v --tb=short
```

Expected: all pass

**Step 6: Commit**

```bash
git add src/neuro_mcp/service.py tests/test_service_thread_safety.py
git commit -m "fix(concurrency): add threading lock to service.refresh() to prevent race conditions"
```

---

### Task 3: Replace brittle pyproject.toml string hacking with `tomllib`

**Background:** `codebase.py:104–114` extracts dependencies from `pyproject.toml` using line-by-line string heuristics. It misses `[tool.poetry.dependencies]`, multi-line arrays, and extras. Python 3.11 (the project minimum) ships `tomllib` in the standard library — use it instead.

**Files:**
- Modify: `src/neuro_mcp/codebase.py` (the `elif file_name == "pyproject.toml":` block)
- Create: `tests/test_toml_extraction.py`

**Step 1: Write the failing test**

```python
# tests/test_toml_extraction.py
"""Test dependency extraction from pyproject.toml."""
from __future__ import annotations

from neuro_mcp.codebase import extract_dependencies


PYPROJECT_PEP517 = """
[project]
name = "myapp"
dependencies = [
    "pydantic>=2.0",
    "numpy>=1.26,<3",
    "scikit-learn>=1.4",
]

[project.optional-dependencies]
dev = ["pytest>=8", "coverage"]
mcp = ["mcp>=1.26,<2", "uvicorn>=0.30"]
"""

PYPROJECT_POETRY = """
[tool.poetry]
name = "myapp"

[tool.poetry.dependencies]
python = "^3.11"
pydantic = "^2.7"
numpy = "^1.26"

[tool.poetry.dev-dependencies]
pytest = "^8"
"""


def test_pyproject_pep517_dependencies():
    deps = extract_dependencies("pyproject.toml", PYPROJECT_PEP517)
    assert "pydantic" in deps
    assert "numpy" in deps
    assert "scikit-learn" in deps


def test_pyproject_pep517_optional_dependencies():
    deps = extract_dependencies("pyproject.toml", PYPROJECT_PEP517)
    assert "pytest" in deps
    assert "coverage" in deps
    assert "mcp" in deps
    assert "uvicorn" in deps


def test_pyproject_poetry_dependencies():
    deps = extract_dependencies("pyproject.toml", PYPROJECT_POETRY)
    assert "pydantic" in deps
    assert "numpy" in deps


def test_pyproject_invalid_toml_returns_empty():
    deps = extract_dependencies("pyproject.toml", "this is [not valid toml {{{{")
    assert isinstance(deps, set)
    # Should not raise


def test_pyproject_empty_returns_empty():
    deps = extract_dependencies("pyproject.toml", "")
    assert deps == set()
```

**Step 2: Run test to verify it fails**

```bash
cd /Users/benjaminpoersch/Obsidian_new/neuro_mcp/neuro_mcp_server_clean
python -m pytest tests/test_toml_extraction.py -v --tb=short
```

Expected: multiple FAIL — existing heuristic misses most cases.

**Step 3: Write minimal implementation**

In `src/neuro_mcp/codebase.py`, replace the entire `elif file_name == "pyproject.toml":` block (lines 104–114):

```python
    elif file_name == "pyproject.toml":
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if '"' in line and ("dependencies" in raw_line.lower() or raw_line.strip().startswith('"')):
                # conservative TOML dependency extraction
                parts = [part.strip().strip('",') for part in line.split('"') if part.strip()]
                for part in parts:
                    if any(char.isalpha() for char in part) and not part.startswith("["):
                        dep = part.split(">=")[0].split("<=")[0].split("==")[0].split(";")[0].strip()
                        if dep and " " not in dep:
                            deps.add(dep)
            if raw_line.strip().startswith("name ="):
                continue
```

With:

```python
    elif file_name == "pyproject.toml":
        import tomllib
        import re as _re
        _dep_split = _re.compile(r"[><=!~;\[ ]")
        try:
            data = tomllib.loads(text)
        except Exception:
            return deps

        # PEP 517 / pyproject style
        project = data.get("project") or {}
        dep_lists: list = list(project.get("dependencies") or [])
        for extra_deps in (project.get("optional-dependencies") or {}).values():
            if isinstance(extra_deps, list):
                dep_lists.extend(extra_deps)

        # Poetry style
        poetry_deps = (data.get("tool") or {}).get("poetry") or {}
        for section in ("dependencies", "dev-dependencies", "group"):
            section_val = poetry_deps.get(section)
            if isinstance(section_val, dict):
                dep_lists.extend(section_val.keys())

        for raw in dep_lists:
            name = _dep_split.split(str(raw))[0].strip()
            if name and name.lower() not in {"python", ""}:
                deps.add(name)
```

**Step 4: Run test to verify it passes**

```bash
cd /Users/benjaminpoersch/Obsidian_new/neuro_mcp/neuro_mcp_server_clean
python -m pytest tests/test_toml_extraction.py -v --tb=short
```

Expected: all 5 PASS

**Step 5: Run full suite**

```bash
cd /Users/benjaminpoersch/Obsidian_new/neuro_mcp/neuro_mcp_server_clean
python -m pytest tests/ -v --tb=short
```

Expected: all pass

**Step 6: Commit**

```bash
git add src/neuro_mcp/codebase.py tests/test_toml_extraction.py
git commit -m "fix(parsing): replace brittle pyproject.toml heuristics with tomllib"
```

---

### Task 4: Fix `go.mod` multi-line `require` block parsing

**Background:** `codebase.py:130–136` only handles single-line `require module v1.0.0` statements. The standard Go multi-line form:
```
require (
    github.com/some/dep v1.2.3
    github.com/other/dep v0.9.0
)
```
is never parsed, so all multi-dep Go modules silently report zero dependencies, breaking reconcile for Go projects.

**Files:**
- Modify: `src/neuro_mcp/codebase.py` (the `elif file_name == "go.mod":` block)
- Create: `tests/test_gomod_extraction.py`

**Step 1: Write the failing test**

```python
# tests/test_gomod_extraction.py
"""Test dependency extraction from go.mod files."""
from __future__ import annotations

from neuro_mcp.codebase import extract_dependencies


GO_MOD_SINGLE = """
module github.com/myapp/myapp

go 1.21

require github.com/pkg/errors v0.9.1
require golang.org/x/sync v0.3.0
"""

GO_MOD_BLOCK = """
module github.com/myapp/myapp

go 1.21

require (
\tgithub.com/pkg/errors v0.9.1
\tgolang.org/x/sync v0.3.0
\tgithub.com/stretchr/testify v1.8.4
)
"""

GO_MOD_MIXED = """
module github.com/myapp/myapp

go 1.21

require github.com/single/dep v1.0.0

require (
\tgithub.com/block/dep v2.0.0
\tgithub.com/another/dep v3.0.0
)
"""

GO_MOD_WITH_INDIRECT = """
module github.com/myapp/myapp

go 1.21

require (
\tgithub.com/direct/dep v1.0.0
\tgithub.com/indirect/dep v2.0.0 // indirect
)
"""


def test_gomod_single_line_require():
    deps = extract_dependencies("go.mod", GO_MOD_SINGLE)
    assert "github.com/pkg/errors" in deps
    assert "golang.org/x/sync" in deps


def test_gomod_block_require():
    deps = extract_dependencies("go.mod", GO_MOD_BLOCK)
    assert "github.com/pkg/errors" in deps
    assert "golang.org/x/sync" in deps
    assert "github.com/stretchr/testify" in deps


def test_gomod_mixed_require():
    deps = extract_dependencies("go.mod", GO_MOD_MIXED)
    assert "github.com/single/dep" in deps
    assert "github.com/block/dep" in deps
    assert "github.com/another/dep" in deps


def test_gomod_indirect_deps_included():
    deps = extract_dependencies("go.mod", GO_MOD_WITH_INDIRECT)
    assert "github.com/direct/dep" in deps
    assert "github.com/indirect/dep" in deps


def test_gomod_empty():
    deps = extract_dependencies("go.mod", "module foo\ngo 1.21\n")
    assert isinstance(deps, set)
```

**Step 2: Run test to verify it fails**

```bash
cd /Users/benjaminpoersch/Obsidian_new/neuro_mcp/neuro_mcp_server_clean
python -m pytest tests/test_gomod_extraction.py -v --tb=short
```

Expected: `test_gomod_block_require`, `test_gomod_mixed_require` FAIL — block form is not parsed.

**Step 3: Write minimal implementation**

In `src/neuro_mcp/codebase.py`, replace the `elif file_name == "go.mod":` block (lines 130–136):

```python
    elif file_name == "go.mod":
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if line.startswith("require "):
                dep = line.removeprefix("require ").split(" ")[0].strip()
                if dep:
                    deps.add(dep)
```

With:

```python
    elif file_name == "go.mod":
        in_require_block = False
        for raw_line in text.splitlines():
            line = raw_line.strip()
            # Enter multi-line require block
            if line.startswith("require") and "(" in line:
                in_require_block = True
                continue
            # Exit multi-line require block
            if in_require_block and line == ")":
                in_require_block = False
                continue
            # Inside block: each line is "module/path vX.Y.Z [// indirect]"
            if in_require_block and line and not line.startswith("//"):
                dep = line.split()[0].strip()
                if dep:
                    deps.add(dep)
                continue
            # Single-line require: "require module/path vX.Y.Z"
            if line.startswith("require ") and "(" not in line:
                parts = line.removeprefix("require ").split()
                if parts:
                    deps.add(parts[0].strip())
```

**Step 4: Run test to verify it passes**

```bash
cd /Users/benjaminpoersch/Obsidian_new/neuro_mcp/neuro_mcp_server_clean
python -m pytest tests/test_gomod_extraction.py -v --tb=short
```

Expected: 5 PASS

**Step 5: Run full suite**

```bash
cd /Users/benjaminpoersch/Obsidian_new/neuro_mcp/neuro_mcp_server_clean
python -m pytest tests/ -v --tb=short
```

Expected: all pass

**Step 6: Commit**

```bash
git add src/neuro_mcp/codebase.py tests/test_gomod_extraction.py
git commit -m "fix(parsing): handle go.mod multi-line require blocks"
```

---

### Task 5: Document `data_dir` security constraint (joblib pickle)

**Background:** `embeddings.py:49` uses `joblib.load()` which deserializes pickle. There is no practical safe alternative that preserves the TF-IDF vectorizer without pickle (sklearn's own serialization is pickle-based). The correct mitigation is to ensure `data_dir` is not world-writable and to document this constraint clearly. This task adds an explicit check at startup and a note in the config schema.

**Files:**
- Modify: `src/neuro_mcp/service.py` (add startup check in `__init__`)
- Modify: `src/neuro_mcp/config.py` (add docstring to `data_dir` field)
- Create: `tests/test_data_dir_permissions.py`

**Step 1: Write the failing test**

```python
# tests/test_data_dir_permissions.py
"""Test that service warns when data_dir is world-writable."""
from __future__ import annotations

import logging
import os
import stat
from pathlib import Path

import pytest

from neuro_mcp.config import Settings
from neuro_mcp.service import NeuroMCPService


@pytest.mark.skipif(os.name == "nt", reason="chmod not meaningful on Windows")
def test_service_warns_on_world_writable_data_dir(tmp_path: Path, caplog):
    brain = tmp_path / "brain"
    brain.mkdir()
    code = tmp_path / "code"
    code.mkdir()
    data = tmp_path / "data"
    data.mkdir()

    # Make data_dir world-writable
    data.chmod(data.stat().st_mode | stat.S_IWOTH)

    settings = Settings(brain_root=brain, code_root=code, data_dir=data)
    with caplog.at_level(logging.WARNING, logger="neuro_mcp.service"):
        NeuroMCPService(settings)

    assert any(
        "world-writable" in r.message.lower() or "data_dir" in r.message.lower()
        for r in caplog.records
    ), f"Expected world-writable warning, got: {[r.message for r in caplog.records]}"

    # Cleanup: restore permissions
    data.chmod(data.stat().st_mode & ~stat.S_IWOTH)
```

**Step 2: Run test to verify it fails**

```bash
cd /Users/benjaminpoersch/Obsidian_new/neuro_mcp/neuro_mcp_server_clean
python -m pytest tests/test_data_dir_permissions.py -v --tb=short
```

Expected: FAIL — no warning logged.

**Step 3: Write minimal implementation**

Add `import logging` and `import os` and `import stat` to `src/neuro_mcp/service.py` imports (add to the existing imports at the top):

```python
import logging
import os
import stat
```

Add `logger = logging.getLogger(__name__)` after the imports.

In `NeuroMCPService.__init__`, after `self._refresh_lock = threading.Lock()`, add:

```python
        self._check_data_dir_permissions()
```

Add the new method to `NeuroMCPService` (before `refresh`):

```python
    def _check_data_dir_permissions(self) -> None:
        """Warn if data_dir is world-writable — joblib uses pickle, which is unsafe if writable by others."""
        data_dir = self.settings.data_dir
        if not data_dir.exists():
            return
        if os.name == "nt":
            return  # Windows permissions model is different
        try:
            mode = data_dir.stat().st_mode
            if mode & stat.S_IWOTH:
                logger.warning(
                    "data_dir '%s' is world-writable. "
                    "joblib index files use pickle — a malicious actor with write access "
                    "could execute arbitrary code on load. "
                    "Fix with: chmod o-w '%s'",
                    data_dir,
                    data_dir,
                )
        except OSError:
            pass
```

**Step 4: Run test to verify it passes**

```bash
cd /Users/benjaminpoersch/Obsidian_new/neuro_mcp/neuro_mcp_server_clean
python -m pytest tests/test_data_dir_permissions.py -v --tb=short
```

Expected: PASS

**Step 5: Run full suite**

```bash
cd /Users/benjaminpoersch/Obsidian_new/neuro_mcp/neuro_mcp_server_clean
python -m pytest tests/ -v --tb=short
```

Expected: all pass

**Step 6: Commit**

```bash
git add src/neuro_mcp/service.py tests/test_data_dir_permissions.py
git commit -m "fix(security): warn at startup when data_dir is world-writable (pickle risk)"
```

---

### Task 6: End-to-End Verification

**Step 1: Run full test suite**

```bash
cd /Users/benjaminpoersch/Obsidian_new/neuro_mcp/neuro_mcp_server_clean
python -m pytest tests/ -v --tb=short
```

Expected: all pass

**Step 2: Syntax-check all modified modules**

```bash
cd /Users/benjaminpoersch/Obsidian_new/neuro_mcp/neuro_mcp_server_clean
python -m py_compile \
  src/neuro_mcp/watcher.py \
  src/neuro_mcp/service.py \
  src/neuro_mcp/codebase.py
```

Expected: no output (no errors)

**Step 3: Verify the CLI still imports cleanly**

```bash
cd /Users/benjaminpoersch/Obsidian_new/neuro_mcp/neuro_mcp_server_clean
python -c "from neuro_mcp.cli import build_parser; build_parser(); print('CLI OK')"
```

Expected: `CLI OK`

**Step 4: Smoke-test the service with example data**

```bash
cd /Users/benjaminpoersch/Obsidian_new/neuro_mcp/neuro_mcp_server_clean
pip install -e . -q
neuro-mcp --config config.example.yaml index
neuro-mcp --config config.example.yaml status
```

Expected: JSON output with `total_notes` > 0, no exceptions.

**Step 5: Commit summary tag**

```bash
git tag fixes/async-thread-parsing-2026-04-10
```
