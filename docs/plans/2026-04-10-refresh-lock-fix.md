# Refresh Lock Bug Fix Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix the pre-existing SQLite race condition that causes `test_concurrent_refresh_and_search_do_not_raise` to fail intermittently.

**Architecture:** Replace the single shared SQLite connection with a connection pool (one per thread via `threading.local`). This is the standard Python/SQLite pattern and avoids the need to serialize all reads behind the refresh lock. The `Repository` class already uses `check_same_thread=False`; we replace the shared `self._conn` with a thread-local cache so each thread gets its own connection. SQLite handles per-connection concurrency correctly.

**Tech Stack:** Python 3.11+, sqlite3 (stdlib), threading.local, pytest

---

## Problem Statement

**Symptom:** `tests/test_service_thread_safety.py::test_concurrent_refresh_and_search_do_not_raise` fails intermittently. Baseline fail rate ~7%, after Phase 3 changes ~57%.

**Root cause:** `Repository._get_conn()` caches a single `sqlite3.Connection` instance in `self._conn` and shares it across all threads (`check_same_thread=False`). When `refresh()` calls `replace_kind()` (which does `DELETE` then `executemany INSERT` then `commit`), and `search_brain()` simultaneously calls `all_documents()` which does `execute("SELECT ...")`, both threads hit the same connection. SQLite handles some overlapping reads but not while another thread is mid-`executemany` batch — the second thread either sees an incomplete result set or hits an internal state assertion.

**Why this test got flakier in Phase 3:** The new `_run_pipeline_stage` wrapper shifted the timing of `refresh()` enough that the race window opened wider.

**Why not just acquire the refresh lock in search?** It would work but it serializes ALL reads during any refresh. On a multi-agent setup with dozens of concurrent MCP clients, one refresh blocks every query. Connection-per-thread is the idiomatic fix.

---

### Task 1: Reproduce the flaky test reliably

**Files:**
- Test: `tests/test_service_thread_safety.py`

**Step 1: Run the test 30 times to establish baseline failure rate**

```bash
for i in {1..30}; do uv run pytest tests/test_service_thread_safety.py -q --no-header 2>&1 | tail -1; done
```

Expected: Some runs show `1 failed`, some show `1 passed`. Record the failure count (e.g., "17/30 fail").

**Step 2: Increase stress in the test to make failure deterministic**

The current test does 5 refresh iterations and 10 search iterations per thread. Increase to expose the race more reliably.

Modify `tests/test_service_thread_safety.py`:

Replace the `do_refresh` and `do_search` functions and the threads list:

```python
    def do_refresh():
        for _ in range(20):
            try:
                svc.refresh()
            except Exception as exc:
                errors.append(exc)
            time.sleep(0.001)

    def do_search():
        for _ in range(50):
            try:
                svc.search_brain("testing", top_k=3)
            except Exception as exc:
                errors.append(exc)
            time.sleep(0.001)

    threads = [
        threading.Thread(target=do_refresh),
        threading.Thread(target=do_refresh),
        threading.Thread(target=do_search),
        threading.Thread(target=do_search),
        threading.Thread(target=do_search),
        threading.Thread(target=do_search),
    ]
```

**Step 3: Verify test now fails reliably (before fix)**

```bash
for i in {1..10}; do uv run pytest tests/test_service_thread_safety.py -q --no-header 2>&1 | tail -1; done
```

Expected: Most runs fail (≥ 7/10). If it still passes most runs, increase iteration counts further.

**Step 4: Do NOT commit yet**

The test modifications are part of Task 3's commit. Keep the change staged for now.

---

### Task 2: Replace shared connection with thread-local pool

**Files:**
- Modify: `src/neuro_mcp/storage.py`

**Step 1: Import threading**

At the top of `src/neuro_mcp/storage.py`, add:

```python
import threading
```

The file currently imports `json`, `sqlite3`, `Path`, `Iterable`, `DocKind`, `DocumentRecord`. Keep those.

**Step 2: Replace the `_conn` attribute with a thread-local pool**

Find the `Repository.__init__` method:

```python
class Repository:
    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: sqlite3.Connection | None = None
        self._init()
```

Replace with:

```python
class Repository:
    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._local = threading.local()
        self._all_connections: list[sqlite3.Connection] = []
        self._all_connections_lock = threading.Lock()
        self._init()
```

**Step 3: Replace `_get_conn` with thread-local version**

Find `_get_conn`:

```python
    def _get_conn(self) -> sqlite3.Connection:
        """Return the cached connection, creating it if needed."""
        if self._conn is None:
            self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
        return self._conn
```

Replace with:

```python
    def _get_conn(self) -> sqlite3.Connection:
        """Return the current thread's connection, creating it on first use."""
        conn = getattr(self._local, "conn", None)
        if conn is None:
            conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
            conn.row_factory = sqlite3.Row
            self._local.conn = conn
            with self._all_connections_lock:
                self._all_connections.append(conn)
        return conn
```

**Step 4: Update `close` to close all connections**

Find `close`:

```python
    def close(self) -> None:
        """Close the cached connection."""
        if self._conn is not None:
            self._conn.close()
            self._conn = None
```

Replace with:

```python
    def close(self) -> None:
        """Close all thread-local connections."""
        with self._all_connections_lock:
            for conn in self._all_connections:
                try:
                    conn.close()
                except sqlite3.Error:
                    pass
            self._all_connections.clear()
        self._local = threading.local()
```

**Step 5: Run existing non-concurrency tests to verify no regressions**

```bash
uv run pytest tests/test_storage_connection.py -v
```

Expected: 3 passed (test_repository_reuses_connection, test_repository_close_releases_connection, test_repository_operations_after_close).

If `test_repository_reuses_connection` fails because it checks `self._conn`, read the test and update it to check the thread-local cache instead. Since that test runs on a single thread, `_get_conn()` should still return the same connection across calls.

**Step 6: Run full test suite**

```bash
uv run pytest 2>&1 | tail -5
```

Expected: All pass except possibly the stressed thread-safety test (which we'll verify in Task 3).

---

### Task 3: Verify the fix resolves the race

**Files:**
- Test: `tests/test_service_thread_safety.py` (already modified in Task 1)

**Step 1: Run the stressed test 20 times**

```bash
for i in {1..20}; do uv run pytest tests/test_service_thread_safety.py -q --no-header 2>&1 | tail -1; done
```

Expected: All 20 runs pass (`1 passed`).

**Step 2: If failures remain, diagnose**

If any run fails, look at the error. Possible remaining issues:

- **SQLite database locked**: thread B tries to write while A holds a write lock. Fix: set SQLite WAL mode on connection creation. In `_get_conn`, after `conn.row_factory = sqlite3.Row`, add:
  ```python
  conn.execute("PRAGMA journal_mode=WAL")
  conn.execute("PRAGMA busy_timeout=5000")
  ```

- **Stale in-memory notes dict**: `service.search_brain` reads `self.repo.all_documents()` which now works from an isolated connection, but also touches `self.notes` which is replaced mid-refresh. That's a separate race on Python dict mutation. If this shows up: guard the `self.notes = notes` assignment at the end of refresh by swapping atomically (assign a new dict, don't mutate in place).

**Step 3: Run full suite one more time**

```bash
uv run pytest 2>&1 | tail -5
```

Expected: 109+ passed, 1 skipped, 0 failed.

**Step 4: Commit**

```bash
git add src/neuro_mcp/storage.py tests/test_service_thread_safety.py
git commit -m "$(cat <<'EOF'
fix(storage): thread-local SQLite connection pool to resolve refresh/search race

Previously Repository shared a single sqlite3.Connection across all threads
via check_same_thread=False. Concurrent search_brain() and refresh() calls
race on the same connection mid-transaction, causing intermittent failures
in test_concurrent_refresh_and_search_do_not_raise.

Fix: one connection per thread via threading.local. The
test_concurrent_refresh_and_search_do_not_raise test is also stressed
(6 threads, 20/50 iterations) to reliably detect future regressions.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)"
```

---

### Task 4: Add a tracker entry and update docs

**Files:**
- Modify: `3-code/tasks.md`
- Modify: `CLAUDE.md`

**Step 1: Add TASK-storage-thread-local to tasks.md**

In the Core Engine task table, after the pipeline-metrics rows, add:

```
| TASK-storage-thread-local | Thread-local SQLite connection pool for concurrent refresh/search | P0 | Done | - | - | 2026-04-10 | Fixes flaky test_concurrent_refresh_and_search_do_not_raise |
```

**Step 2: Update CLAUDE.md Current State**

Find the line `Implementation progress: 19/50 tasks done`. Update to `20/51 tasks done`.

**Step 3: Commit**

```bash
git add 3-code/tasks.md CLAUDE.md
git commit -m "$(cat <<'EOF'
chore: record storage thread-local fix in task tracker

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Summary

| Task | Type | Est. Time |
|------|------|-----------|
| 1. Reproduce flaky test reliably | Test | 5 min |
| 2. Thread-local connection pool | Fix | 10 min |
| 3. Verify fix + commit | Verification | 5 min |
| 4. Update tracker | Admin | 2 min |

**Total: ~25 min, 2 commits.**

## Risks & Notes

- **Connection leak risk:** Each thread gets its own connection. In long-lived services with many short-lived threads, connections accumulate. Mitigation: the current codebase uses a small, stable thread pool (watcher + main thread + few HTTP workers), so the pool stays small. If this becomes a problem, add explicit cleanup on thread exit.

- **WAL mode consideration:** If step 3.2 reveals "database is locked" errors, enabling WAL mode is the standard fix. Noted as a fallback.

- **Why not use `refresh_lock` in `search_brain()`:** Simpler but serializes all searches during any refresh. For a knowledge engine with potentially many concurrent AI clients, this is the wrong tradeoff. Thread-local is the right fix.

- **Existing tests using `_conn`:** `test_storage_connection.py` tests might reference `self._conn`. Check and update if needed in Task 2 Step 5.
