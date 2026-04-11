# Pipeline Refactor & Review Gaps Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Address 3 missing integration tests, extract pipeline stages from `service.py` into a dedicated `pipeline.py` module, write the Phase 3.5 manual testing runbook (including the watcher self-healing loop documentation), and add a small benchmark for enrichment throughput.

**Architecture:** Keep `NeuroMCPService` focused on orchestration + state; move stage implementation logic into `src/neuro_mcp/pipeline.py` as free functions that take state as parameters. Service methods become thin adapters. No public API changes. Tests stay passing throughout.

**Tech Stack:** Python 3.11+, pytest, Pydantic

---

## Design Decisions (Q1/Q2)

**Q1 (enrichment throughput):** Add a microbenchmark test with `N=100` notes that asserts enrichment completes in < 2 seconds on the local machine. Good enough for MVP. No Prometheus/performance regression CI yet — defer until real data shows it matters.

**Q2 (write storm on large vault):** The self-healing loop (enrich → watcher fires → re-enrich → no-op → steady state) is the answer. Maximum 2 refresh cycles on a cold vault. **No code change needed** — just document it in the runbook so operators understand the behavior.

**Refactor approach:** Extract pipeline functions into `pipeline.py` as **module-level free functions** that take explicit parameters (`notes`, `settings`, etc.). Service methods become 1-line wrappers. This:
- Keeps public API unchanged (no test breakage)
- Makes each function independently unit-testable
- Removes state dependency from the core logic
- Prevents service.py from becoming a god class

---

### Task 1: Add missing integration test — STC sees enriched notes

**Files:**
- Test: `tests/test_auto_frontmatter_pipeline.py` (append to existing file)

**Step 1: Write the test**

Append to `tests/test_auto_frontmatter_pipeline.py`:

```python
def test_stc_sees_enriched_inbox_notes():
    """Pipeline ordering: enrich runs before STC, so bare notes in 00-inbox
    get type:inbox, decay_class:7d BEFORE STC evaluates them for promotion."""
    import subprocess
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        brain = tdp / "brain"
        code = tdp / "code"
        brain.mkdir()
        code.mkdir()
        # Git-init code so changed_files_since has something to read
        subprocess.run(["git", "init", "-q"], cwd=code, check=True)
        (code / "src").mkdir()
        src_file = code / "src" / "auth.py"
        src_file.write_text("def login(): pass\n")
        subprocess.run(["git", "add", "."], cwd=code, check=True)
        subprocess.run(
            ["git", "-c", "user.email=t@t.io", "-c", "user.name=t", "commit", "-qm", "init"],
            cwd=code, check=True,
        )

        # Bare note in 00-inbox with linked_paths pointing at the just-changed file
        inbox_note = brain / "00-inbox" / "auth-note.md"
        inbox_note.parent.mkdir()
        inbox_note.write_text(
            "---\nlinked_paths: [src/auth.py]\n---\nFresh auth notes.\n"
        )

        settings = _settings(
            tdp,
            enable_auto_enrich_frontmatter=True,
            enable_stc=True,
            folder_type_map={
                "00-inbox": {"type": "inbox", "decay_class": "7d"},
            },
        )
        svc = NeuroMCPService(settings)
        svc.refresh()

        # After refresh, note should be enriched (type:inbox, decay:7d) AND
        # STC stage should have run without errors (even if no promotion happens)
        meta, _ = parse_markdown_note(inbox_note)
        assert meta["type"] == "inbox"
        assert meta["decay_class"] == "7d"

        digest = svc.digest()
        stc_stage = next((s for s in digest.pipeline_stages if s.stage == "stc"), None)
        assert stc_stage is not None
        assert stc_stage.error_count == 0
```

**Step 2: Run test**

```bash
uv run pytest tests/test_auto_frontmatter_pipeline.py::test_stc_sees_enriched_inbox_notes -v
```
Expected: PASS (enrichment already runs before STC per the current pipeline ordering).

**Step 3: Commit**

```bash
git add tests/test_auto_frontmatter_pipeline.py
git commit -m "test: verify STC stage runs cleanly after enrichment stage"
```

---

### Task 2: Add symlink safety test

**Files:**
- Test: `tests/test_auto_frontmatter_pipeline.py` (append)

**Step 1: Write the test**

Append:

```python
def test_symlink_outside_brain_root_is_skipped():
    """Notes resolving outside brain_root (via symlink) are skipped defensively."""
    import os
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        brain = tdp / "brain"
        outside = tdp / "outside"
        brain.mkdir()
        outside.mkdir()

        # Real file outside brain_root
        real_note = outside / "escaped.md"
        real_note.write_text("Escaped content.\n")

        # Symlink inside brain_root pointing at it
        symlink_note = brain / "via-symlink.md"
        try:
            os.symlink(real_note, symlink_note)
        except OSError:
            import pytest
            pytest.skip("Symlinks not supported on this filesystem")

        settings = _settings(tdp, enable_auto_enrich_frontmatter=True)
        svc = NeuroMCPService(settings)
        svc.refresh()  # must not raise

        # The escaped file should NOT have been enriched
        assert "_neuro_mcp_enriched" not in real_note.read_text()
```

**Step 2: Run**

```bash
uv run pytest tests/test_auto_frontmatter_pipeline.py::test_symlink_outside_brain_root_is_skipped -v
```
Expected: PASS — `ValueError` in `_run_auto_frontmatter_enrich` is caught and the note is skipped.

**Step 3: Commit**

```bash
git add tests/test_auto_frontmatter_pipeline.py
git commit -m "test: symlinks resolving outside brain_root are skipped by enrichment"
```

---

### Task 3: Add `logger.debug` to the symlink skip branch (L-3 fix)

**Files:**
- Modify: `src/neuro_mcp/service.py:203-204` (inside `_run_auto_frontmatter_enrich`)

**Step 1: Add the log line**

Change:
```python
            try:
                relative = note_path.resolve().relative_to(brain_root)
            except ValueError:
                continue  # Note outside brain_root — skip defensively
```

to:
```python
            try:
                relative = note_path.resolve().relative_to(brain_root)
            except ValueError:
                logger.debug("Skipping note outside brain_root: %s", note_path)
                continue
```

**Step 2: Run all tests**

```bash
uv run pytest 2>&1 | tail -3
```
Expected: All pass.

**Step 3: Commit**

```bash
git add src/neuro_mcp/service.py
git commit -m "chore: log debug message when enrichment skips note outside brain_root"
```

---

### Task 4: Add enrichment throughput benchmark (Q1 answer)

**Files:**
- Test: `tests/test_auto_frontmatter_pipeline.py` (append)

**Step 1: Write the benchmark test**

```python
def test_enrichment_throughput_100_notes():
    """Enrichment of 100 bare notes should complete in < 2 seconds.

    This is a loose bound — the real purpose is to catch ~10x regressions,
    not fine-grained performance tuning.
    """
    import time
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        brain = tdp / "brain" / "04-projekte"
        brain.mkdir(parents=True)
        for i in range(100):
            (brain / f"note-{i:03d}.md").write_text(f"Body of note {i}\n")

        settings = _settings(
            tdp,
            enable_auto_enrich_frontmatter=True,
            folder_type_map={
                "04-projekte": {"type": "note", "decay_class": "30d"},
            },
        )
        svc = NeuroMCPService(settings)

        start = time.perf_counter()
        svc.refresh()
        elapsed = time.perf_counter() - start

        assert elapsed < 2.0, f"Enrichment of 100 notes took {elapsed:.2f}s"

        # Verify all 100 were actually enriched
        enriched_count = sum(
            1 for p in brain.glob("*.md")
            if "_neuro_mcp_enriched" in p.read_text()
        )
        assert enriched_count == 100
```

**Step 2: Run**

```bash
uv run pytest tests/test_auto_frontmatter_pipeline.py::test_enrichment_throughput_100_notes -v
```
Expected: PASS. Print the actual elapsed time via `-v` for reference.

**Step 3: Commit**

```bash
git add tests/test_auto_frontmatter_pipeline.py
git commit -m "test: enrichment throughput benchmark (100 notes < 2s)"
```

---

### Task 5: Extract pipeline functions into `pipeline.py`

**Files:**
- Create: `src/neuro_mcp/pipeline.py`
- Modify: `src/neuro_mcp/service.py`

**Step 1: Create the new module**

Create `src/neuro_mcp/pipeline.py` with the extracted functions. Each takes explicit parameters — no `self`.

```python
"""Pipeline stage implementations for refresh()."""
from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any, Callable, Iterable

from .config import Settings
from .frontmatter import (
    dump_markdown_note,
    enrich_note_frontmatter,
    parse_markdown_note,
)
from .git_utils import changed_files_since
from .models import Mode, NoteMetadata, NoteStatus, PipelineStageResult
from .synaptic_tagging import evaluate_promotions

logger = logging.getLogger(__name__)


def run_pipeline_stage(
    name: str,
    fn: Callable[[], Any],
    enabled: bool,
) -> PipelineStageResult | None:
    """Run a pipeline stage, record metrics, isolate errors.

    Returns the result for appending to a stage list, or None if disabled.
    """
    if not enabled:
        return None
    start = time.perf_counter()
    result = PipelineStageResult(stage=name)
    try:
        out = fn()
        if isinstance(out, list):
            result.items_processed = len(out)
    except Exception:
        logger.exception("Pipeline stage %r failed", name)
        result.error_count = 1
    result.duration_ms = (time.perf_counter() - start) * 1000
    return result


def check_labile_linked_paths(
    notes: dict[str, NoteMetadata],
    settings: Settings,
) -> list[str]:
    """Mark notes labile when their linked_paths reference deleted files.

    Returns the list of note paths that were marked labile.
    """
    if not settings.auto_mark_labile:
        return []
    marked: list[str] = []
    for note in notes.values():
        if not note.linked_paths:
            continue
        missing = [
            p for p in note.linked_paths
            if not (settings.code_root / p).exists()
        ]
        if missing and note.status == NoteStatus.ACTIVE:
            note_path = Path(note.path)
            if not note_path.exists():
                continue
            meta, body = parse_markdown_note(note_path)
            meta["status"] = "labile"
            meta["labile_reasons"] = [f"linked file deleted: {p}" for p in missing]
            note_path.write_text(dump_markdown_note(meta, body), encoding="utf-8")
            logger.info("Marked labile: %s (missing: %s)", note.path, missing)
            marked.append(str(note_path))
    return marked


def run_stc_promotions(
    notes: dict[str, NoteMetadata],
    settings: Settings,
) -> list[dict]:
    """Evaluate and apply STC promotions for inbox notes."""
    try:
        changed = set(changed_files_since(settings.code_root))
    except Exception:
        changed = set()
    if not changed:
        return []
    promotions = evaluate_promotions(
        notes=notes,
        changed_files=changed,
        stc_window_hours=settings.stc_window_hours,
    )
    for promo in promotions:
        note_path = Path(promo["path"])
        if not note_path.exists():
            continue
        meta, body = parse_markdown_note(note_path)
        meta["decay_class"] = promo["new_decay_class"]
        note_path.write_text(dump_markdown_note(meta, body), encoding="utf-8")
        logger.info(
            "STC promoted: %s (%s -> %s): %s",
            promo["title"], promo["old_decay_class"],
            promo["new_decay_class"], promo["reason"],
        )
    return promotions


def run_auto_frontmatter_enrich(
    notes: dict[str, NoteMetadata],
    settings: Settings,
) -> list[str]:
    """Fill in missing frontmatter fields for all brain notes.

    Returns the list of note paths that were modified.
    """
    enriched: list[str] = []
    brain_root = settings.brain_root.resolve()
    for note in notes.values():
        note_path = Path(note.path)
        if not note_path.exists():
            continue
        try:
            relative = note_path.resolve().relative_to(brain_root)
        except ValueError:
            logger.debug("Skipping note outside brain_root: %s", note_path)
            continue
        rule = settings.resolve_folder_type(relative)
        if enrich_note_frontmatter(note_path, rule=rule):
            enriched.append(str(note_path))
            logger.info("Enriched frontmatter: %s", relative)
    return enriched


def run_auto_reconcile(
    notes: dict[str, NoteMetadata],
    settings: Settings,
    reconcile_fn: Callable[[str], Any],
) -> None:
    """Trigger reconcile on notes whose linked_paths overlap with recently changed files."""
    try:
        changed = set(changed_files_since(settings.code_root))
    except Exception:
        changed = set()
    if not changed:
        return
    notes_to_reconcile = [
        note for note in notes.values()
        if note.linked_paths and any(p in changed for p in note.linked_paths)
    ]
    if not notes_to_reconcile:
        return
    logger.info("Auto-reconcile triggered for %d note(s)", len(notes_to_reconcile))
    for note in notes_to_reconcile:
        try:
            reconcile_fn(note.title)
        except Exception:
            logger.exception("Reconcile failed for note: %s", note.path)
```

**Step 2: Replace service.py methods with thin wrappers**

In `src/neuro_mcp/service.py`:

1. Add import at top:
```python
from . import pipeline
```

2. Replace `_check_labile_linked_paths`, `_run_stc_promotions`, `_run_auto_frontmatter_enrich`, `_run_auto_reconcile`, `_run_pipeline_stage` method bodies. The methods become one-line delegations:

```python
    def _check_labile_linked_paths(self) -> list[str]:
        return pipeline.check_labile_linked_paths(self.notes, self.settings)

    def _run_stc_promotions(self) -> list[dict]:
        promotions = pipeline.run_stc_promotions(self.notes, self.settings)
        self._recent_promotions = promotions
        return promotions

    def _run_auto_frontmatter_enrich(self) -> list[str]:
        return pipeline.run_auto_frontmatter_enrich(self.notes, self.settings)

    def _run_auto_reconcile(self) -> None:
        pipeline.run_auto_reconcile(self.notes, self.settings, self.reconcile)

    def _run_pipeline_stage(self, name: str, fn, enabled: bool) -> None:
        result = pipeline.run_pipeline_stage(name, fn, enabled)
        if result is not None:
            self._pipeline_stages.append(result)
```

3. Remove the now-unused imports from service.py (if any): `evaluate_promotions`, `changed_files_since`, `enrich_note_frontmatter`. Check which are still needed by other methods.

**Step 3: Run full suite**

```bash
uv run pytest 2>&1 | tail -5
```
Expected: All tests pass (141+ now).

**Step 4: Commit**

```bash
git add src/neuro_mcp/pipeline.py src/neuro_mcp/service.py
git commit -m "refactor: extract pipeline stage functions into pipeline.py module

service.py methods become thin wrappers over free functions in pipeline.py.
No public API changes — all tests pass unchanged. Reduces service.py size
and makes pipeline logic independently testable."
```

---

### Task 6: Add unit tests for pipeline module

**Files:**
- Create: `tests/test_pipeline_module.py`

**Step 1: Write tests for the new free functions**

```python
"""Direct unit tests for pipeline module free functions (no service wiring)."""
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

from neuro_mcp import pipeline
from neuro_mcp.config import Settings
from neuro_mcp.frontmatter import dump_markdown_note


def _settings(td: Path) -> Settings:
    brain = td / "brain"
    code = td / "code"
    brain.mkdir(exist_ok=True)
    code.mkdir(exist_ok=True)
    return Settings(brain_root=brain, code_root=code, data_dir=td / "data")


def test_run_pipeline_stage_disabled_returns_none():
    result = pipeline.run_pipeline_stage("test", lambda: [], enabled=False)
    assert result is None


def test_run_pipeline_stage_success_records_count():
    result = pipeline.run_pipeline_stage("test", lambda: [1, 2, 3], enabled=True)
    assert result is not None
    assert result.items_processed == 3
    assert result.error_count == 0
    assert result.duration_ms >= 0


def test_run_pipeline_stage_error_isolated():
    def failing():
        raise RuntimeError("boom")
    result = pipeline.run_pipeline_stage("test", failing, enabled=True)
    assert result is not None
    assert result.error_count == 1


def test_run_auto_frontmatter_enrich_empty_notes():
    with tempfile.TemporaryDirectory() as td:
        settings = _settings(Path(td))
        enriched = pipeline.run_auto_frontmatter_enrich({}, settings)
        assert enriched == []
```

**Step 2: Run**

```bash
uv run pytest tests/test_pipeline_module.py -v
```
Expected: 4 passed.

**Step 3: Commit**

```bash
git add tests/test_pipeline_module.py
git commit -m "test: unit tests for pipeline module free functions"
```

---

### Task 7: Write Phase 3.5 manual testing runbook

**Files:**
- Create: `4-deploy/runbooks/phase-3-5-mvp.md`

**Step 1: Create the runbook**

```markdown
# Phase 3.5: MVP Auto-Enrichment — Manual Test Runbook

## Prerequisites

```bash
cd /path/to/neuro_mcp_server_clean
uv sync --extra mcp --extra dev
```

## Configuration

Enable the enrichment pipeline in your `config.yaml`:

```yaml
enable_auto_enrich_frontmatter: true
folder_type_map:
  "00-inbox": {type: inbox, decay_class: 7d}
  "04-projekte": {type: note, decay_class: 30d}
  "10-architecture": {type: architecture, decay_class: 90d}
  "20-decisions": {type: adr, decay_class: immutable}
  "50-bugs-fixes": {type: bug, decay_class: 14d}
```

## Test 1: Fresh bare note gets full frontmatter

```bash
mkdir -p /tmp/test-brain/00-inbox
echo "Just a body, no frontmatter." > /tmp/test-brain/00-inbox/new-idea.md

uv run neuro-mcp --brain-root /tmp/test-brain --code-root /tmp/test-brain \
  index
cat /tmp/test-brain/00-inbox/new-idea.md
```

Expected: File now has `title: New Idea`, `type: inbox`, `decay_class: 7d`,
`status: active`, `last_verified: <today>`, `created: <today>`,
`_neuro_mcp_enriched: v1`, `_neuro_mcp_last: <ISO timestamp>`.

## Test 2: Existing user fields preserved

```bash
cat > /tmp/test-brain/00-inbox/user.md <<'EOF'
---
title: My Carefully Chosen Title
type: custom
---

User body content.
EOF

uv run neuro-mcp --brain-root /tmp/test-brain --code-root /tmp/test-brain \
  index
cat /tmp/test-brain/00-inbox/user.md
```

Expected: `title` and `type` unchanged, but `decay_class: 7d`, `status`,
`last_verified`, `created` added.

## Test 3: Self-healing refresh loop (watcher)

The enrichment stage writes back to files, which triggers the file watcher
to fire another refresh. This is **expected behavior** and self-heals:

1. Bare notes → first refresh enriches them → writes trigger watcher → second refresh
2. Second refresh finds nothing new to enrich → steady state

If you see "watcher keeps firing" during heavy enrichment on a fresh vault,
it is normal for the first 1-2 refresh cycles. Steady state is reached
quickly once all notes are enriched.

**To verify:** After a full first enrichment pass, run `neuro-mcp index`
again manually. The second run should not modify any files.

## Test 4: Symlink safety

```bash
mkdir -p /tmp/outside
echo "External content" > /tmp/outside/external.md
ln -s /tmp/outside/external.md /tmp/test-brain/symlinked.md

uv run neuro-mcp --brain-root /tmp/test-brain --code-root /tmp/test-brain \
  index
cat /tmp/outside/external.md
```

Expected: `/tmp/outside/external.md` is **unchanged** — notes resolving
outside `brain_root` are skipped defensively.

## Test 5: Pipeline stage metrics in digest

```bash
uv run neuro-mcp --brain-root /tmp/test-brain --code-root /tmp/test-brain \
  digest
```

Expected output includes a `pipeline_stages` list with at least:
- `enrich_frontmatter` (items_processed = number of notes touched, duration_ms)
- `stc` (items_processed, duration_ms)
- `labile` (items_processed, duration_ms)

## Test 6: Automated tests

```bash
uv run pytest tests/test_auto_frontmatter_enrich.py \
              tests/test_auto_frontmatter_pipeline.py \
              tests/test_pipeline_module.py \
              tests/test_folder_type_map.py -v
```

Expected: All pass.

## Cleanup

```bash
rm -rf /tmp/test-brain /tmp/outside
```

## Known Limitations

- **Stale index window:** After enrichment writes to a file, the SQLite index
  and TF-IDF embedder still reflect the pre-enrichment content until the
  NEXT refresh pass. In practice the watcher fires another refresh within
  the debounce window, so this is typically a 1-cycle gap. CLI `index`
  without the watcher will show the same gap until the next manual run.

- **First-run write storm:** Enabling `enable_auto_enrich_frontmatter` on
  an existing large vault will trigger one refresh pass that writes to every
  unenriched note. Subsequent passes are fast no-ops. Two refresh cycles
  maximum to reach steady state.
```

**Step 2: Commit**

```bash
git add 4-deploy/runbooks/phase-3-5-mvp.md
git commit -m "docs: Phase 3.5 manual test runbook with known limitations"
```

---

### Task 8: Update tracker

**Files:**
- Modify: `3-code/tasks.md`, `CLAUDE.md`

**Step 1: Add tracker rows**

In `3-code/tasks.md` Core Engine table, after `TASK-auto-frontmatter-tests`, add:

```
| TASK-pipeline-module-refactor | Extract pipeline stages into pipeline.py free functions | P2 | Done | - | TASK-auto-frontmatter-refresh-hook | 2026-04-10 | Addresses review god-class concern |
| TASK-pipeline-missing-tests | Add STC-ordering, symlink-safety, and throughput benchmark tests | P2 | Done | - | TASK-auto-frontmatter-refresh-hook | 2026-04-10 | Review gap fix |
```

In Deploy & Operations, mark `TASK-phase-3-5-mvp-manual-testing` as Done:

```
| TASK-phase-3-5-mvp-manual-testing | Create 4-deploy/runbooks/phase-3-5-mvp.md with enrichment test scenarios | P0 | Done | - | ... | 2026-04-10 | |
```

**Step 2: Update CLAUDE.md**

Change "25/69 tasks done" to "28/72 tasks done" (2 new tasks added, 3 total completed in this pass: refactor, missing tests, runbook).

Actually recount: after adding the 2 refactor tasks, total becomes 71. Plus the runbook was already in the list. So: 28/71 done.

Let me recompute: 69 original + 2 new refactor/tests tasks = 71. Completed: 25 + 3 (refactor, missing-tests, runbook) = 28.

**Step 3: Commit**

```bash
git add 3-code/tasks.md CLAUDE.md
git commit -m "chore: track pipeline refactor and runbook tasks (28/71)"
```

---

## Summary

| Task | Type | Time |
|------|------|------|
| 1. STC-ordering integration test | Test | 5 min |
| 2. Symlink safety test | Test | 5 min |
| 3. Logger.debug for skip branch | Fix | 2 min |
| 4. Throughput benchmark test | Test | 5 min |
| 5. Extract pipeline.py module | Refactor | 15 min |
| 6. Unit tests for pipeline module | Test | 5 min |
| 7. Phase 3.5 runbook | Docs | 10 min |
| 8. Tracker updates | Admin | 3 min |

**Total: ~50 min, 8 small commits.**

## Risks

- **Task 5 (refactor):** Most impactful change. Risk of breaking existing tests. Mitigated by the fact that service methods remain as thin wrappers — external API is unchanged.
- **Task 1 (STC integration test):** Requires a git-initialized code_root. If the test environment has git configuration issues, the test may fail. Fallback: simplify to just verify the stage runs without error.

## Expected State After Completion

- 141+ tests passing (6 new: 4 pipeline test cases, 2 integration/benchmark)
- `service.py` reduced by ~60 LOC (5 methods replaced with 1-line wrappers)
- `pipeline.py` module created with 5 free functions
- Phase 3.5 runbook exists with 6 test scenarios + known limitations documented
- Enrichment throughput baseline established (< 2s for 100 notes)
- Task tracker at 28/71 done
