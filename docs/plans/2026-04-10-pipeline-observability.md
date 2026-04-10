# Pipeline Observability & Review Follow-ups Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Address Phase 3 code review findings (S-1 documentation, S-2 startup log) and add pipeline stage observability (counts + timings) to digest/brain_status.

**Architecture:** Minimal additions to the existing pipeline stages. Each stage records a `PipelineStageResult` (name, count, duration_ms, errors). Results are stored on the service and surfaced via `DigestReport`. S-1 is a one-line comment, S-2 is a one-line log at service init.

**Tech Stack:** Python 3.11+, Pydantic, pytest

---

### Task 1: Add S-1 comment explaining pipeline stage ordering

**Files:**
- Modify: `src/neuro_mcp/service.py:141-165` (the refresh() pipeline block)

**Step 1: Add explanatory comment**

In `refresh()`, replace the `# Pipeline stages — each isolated so one failure does not block others` comment with:

```python
# Pipeline stages — order matters: STC first (may promote inbox → 30d),
# then labile (marks status based on linked_paths), then reconcile (read-only).
# Each stage is isolated so one failure does not block others.
```

Also add a comment above `self._loaded = True`:

```python
# Mark loaded before pipeline stages — index is valid even if enrichment fails.
self._loaded = True
```

**Step 2: Commit**

```bash
git add src/neuro_mcp/service.py
git commit -m "docs: explain pipeline stage ordering and _loaded placement"
```

---

### Task 2: Add S-2 startup log when auto-reconcile is enabled

**Files:**
- Modify: `src/neuro_mcp/service.py` (in `__init__`)

**Step 1: Add startup log**

At the end of `NeuroMCPService.__init__()`, after `self._check_data_dir_permissions()`:

```python
if self.settings.enable_auto_reconcile:
    logger.info("Auto-reconcile pipeline stage enabled")
if not self.settings.enable_stc:
    logger.info("STC pipeline stage disabled")
```

**Step 2: Run existing tests to verify no regression**

```bash
uv run pytest tests/test_watcher_config_flags.py tests/test_watcher_pipeline.py -v
```
Expected: All pass

**Step 3: Commit**

```bash
git add src/neuro_mcp/service.py
git commit -m "feat: log pipeline stage config at service startup"
```

---

### Task 3: Create REQ-OBS-pipeline-metrics requirement

**Files:**
- Create: `1-spec/requirements/REQ-OBS-pipeline-metrics.md`
- Modify: `1-spec/CLAUDE.spec.md` (add to requirements index)
- Modify: `1-spec/goals/GOAL-watcher-pipeline.md` (add new req link)

**Step 1: Create the requirement file**

```markdown
# REQ-OBS-pipeline-metrics

**Status:** Draft
**Priority:** Should-have
**Type:** Observability
**Source:** [[1-spec/goals/GOAL-watcher-pipeline|GOAL-watcher-pipeline]]

## Description

The system shall track per-stage metrics (count of items processed, duration in milliseconds, error count) for each pipeline stage (STC, labile, auto-reconcile) and surface them in `digest()` and `brain_status` output, so operators can verify pipeline health and diagnose slow or failing stages.

## Acceptance Criteria

- [ ] Each pipeline stage records: stage name, items_processed, duration_ms, error_count
- [ ] Metrics from the most recent refresh are stored on the service instance
- [ ] `DigestReport` includes a `pipeline_stages` field: list of per-stage metric dicts
- [ ] `brain_status` / digest output shows stage timings and counts
- [ ] When a stage raises, its error_count increments but does not block other stages (already implemented)
- [ ] Metrics are reset on each refresh (represent the latest run, not cumulative)

## Related Artifacts

Goal: [[1-spec/goals/GOAL-watcher-pipeline|GOAL-watcher-pipeline]]
Constraint: [[1-spec/constraints/CON-backwards-compatible|CON-backwards-compatible]]
```

**Step 2: Update 1-spec/CLAUDE.spec.md requirements index**

Add row:
```
| [REQ-OBS-pipeline-metrics](requirements/REQ-OBS-pipeline-metrics.md) | Observability | Should | Draft | Pipeline stage metrics in digest |
```

**Step 3: Update GOAL-watcher-pipeline to link the new req**

In `1-spec/goals/GOAL-watcher-pipeline.md` Related Artifacts, add:
`[[1-spec/requirements/REQ-OBS-pipeline-metrics|REQ-OBS-pipeline-metrics]]`

**Step 4: Commit**

```bash
git add 1-spec/
git commit -m "spec: add REQ-OBS-pipeline-metrics for stage observability"
```

---

### Task 4: Implement PipelineStageResult model

**Files:**
- Modify: `src/neuro_mcp/models.py`
- Test: `tests/test_pipeline_metrics.py`

**Step 1: Write the failing test**

Create `tests/test_pipeline_metrics.py`:

```python
"""Test PipelineStageResult model."""
from neuro_mcp.models import PipelineStageResult


def test_pipeline_stage_result_fields():
    r = PipelineStageResult(
        stage="stc",
        items_processed=3,
        duration_ms=12.5,
        error_count=0,
    )
    assert r.stage == "stc"
    assert r.items_processed == 3
    assert r.duration_ms == 12.5
    assert r.error_count == 0


def test_pipeline_stage_result_defaults():
    r = PipelineStageResult(stage="labile")
    assert r.items_processed == 0
    assert r.duration_ms == 0.0
    assert r.error_count == 0
```

**Step 2: Run to verify it fails**

```bash
uv run pytest tests/test_pipeline_metrics.py -v
```
Expected: FAIL with ImportError on PipelineStageResult

**Step 3: Add the model**

In `src/neuro_mcp/models.py`, add after `DigestReport`:

```python
class PipelineStageResult(BaseModel):
    stage: str
    items_processed: int = 0
    duration_ms: float = 0.0
    error_count: int = 0
```

**Step 4: Run to verify it passes**

```bash
uv run pytest tests/test_pipeline_metrics.py -v
```
Expected: 2 passed

**Step 5: Commit**

```bash
git add src/neuro_mcp/models.py tests/test_pipeline_metrics.py
git commit -m "feat: add PipelineStageResult model for stage metrics"
```

---

### Task 5: Record stage metrics in refresh() pipeline

**Files:**
- Modify: `src/neuro_mcp/service.py` (pipeline block in refresh())
- Modify: `src/neuro_mcp/models.py` (DigestReport adds pipeline_stages field)
- Test: extend `tests/test_pipeline_metrics.py`

**Step 1: Add pipeline_stages field to DigestReport**

In `models.py`, modify `DigestReport`:

```python
class DigestReport(BaseModel):
    generated_at: str
    mode: Mode
    total_notes: int
    stale_notes: int
    labile_notes: int
    missing_source_notes: int
    top_risks: list[str] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)
    promotion_candidates: int = 0
    recent_promotions: int = 0
    pipeline_stages: list[PipelineStageResult] = Field(default_factory=list)
```

**Step 2: Write the failing test**

Add to `tests/test_pipeline_metrics.py`:

```python
import tempfile
import time
from pathlib import Path

from neuro_mcp.config import Settings
from neuro_mcp.frontmatter import dump_markdown_note
from neuro_mcp.service import NeuroMCPService


def _make_note(brain_dir: Path, name: str) -> Path:
    meta = {"title": name, "type": "note", "status": "active", "decay_class": "30d"}
    p = brain_dir / f"{name}.md"
    p.write_text(dump_markdown_note(meta, f"Content of {name}"), encoding="utf-8")
    return p


def test_refresh_records_pipeline_stage_metrics():
    """After refresh, service exposes per-stage metrics via digest()."""
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        brain = tdp / "brain"
        code = tdp / "code"
        brain.mkdir()
        code.mkdir()
        _make_note(brain, "n1")

        settings = Settings(
            brain_root=brain,
            code_root=code,
            data_dir=tdp / "data",
            enable_stc=True,
            enable_auto_reconcile=False,
        )
        svc = NeuroMCPService(settings)
        svc.refresh()
        digest = svc.digest()

        stage_names = {s.stage for s in digest.pipeline_stages}
        assert "stc" in stage_names
        assert "labile" in stage_names
        # auto-reconcile disabled, should not appear
        assert "auto_reconcile" not in stage_names

        for stage in digest.pipeline_stages:
            assert stage.duration_ms >= 0.0


def test_disabled_stage_not_in_metrics():
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        brain = tdp / "brain"
        code = tdp / "code"
        brain.mkdir()
        code.mkdir()
        _make_note(brain, "n1")

        settings = Settings(
            brain_root=brain,
            code_root=code,
            data_dir=tdp / "data",
            enable_stc=False,
            enable_auto_reconcile=False,
        )
        svc = NeuroMCPService(settings)
        svc.refresh()
        digest = svc.digest()

        stage_names = {s.stage for s in digest.pipeline_stages}
        assert "stc" not in stage_names


def test_stage_error_counted():
    """If a stage raises, error_count is 1 but refresh still completes."""
    from unittest.mock import patch
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        brain = tdp / "brain"
        code = tdp / "code"
        brain.mkdir()
        code.mkdir()
        _make_note(brain, "n1")

        settings = Settings(
            brain_root=brain,
            code_root=code,
            data_dir=tdp / "data",
            enable_stc=True,
        )
        svc = NeuroMCPService(settings)
        with patch.object(svc, "_run_stc_promotions", side_effect=RuntimeError("boom")):
            svc.refresh()
        digest = svc.digest()
        stc_stage = next((s for s in digest.pipeline_stages if s.stage == "stc"), None)
        assert stc_stage is not None
        assert stc_stage.error_count == 1
```

**Step 3: Run to verify it fails**

```bash
uv run pytest tests/test_pipeline_metrics.py -v
```
Expected: FAIL — `pipeline_stages` not populated

**Step 4: Modify refresh() to record metrics**

In `service.py`, replace the pipeline block with:

```python
# Pipeline stages — order matters: STC first (may promote inbox → 30d),
# then labile (marks status based on linked_paths), then reconcile (read-only).
# Each stage is isolated so one failure does not block others.
self._pipeline_stages: list[PipelineStageResult] = []
self._run_pipeline_stage("stc", self._run_stc_promotions,
                         enabled=self.settings.enable_stc)
self._run_pipeline_stage("labile", self._check_labile_linked_paths,
                         enabled=True)
self._run_pipeline_stage("auto_reconcile", self._run_auto_reconcile,
                         enabled=self.settings.enable_auto_reconcile)
```

Add the helper method:

```python
def _run_pipeline_stage(self, name: str, fn, enabled: bool) -> None:
    """Run a pipeline stage, record metrics, isolate errors."""
    if not enabled:
        return
    import time
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
    self._pipeline_stages.append(result)
```

Import `PipelineStageResult` at the top of service.py.

Initialize `self._pipeline_stages: list[PipelineStageResult] = []` in `__init__`.

**Step 5: Update digest() to include pipeline_stages**

In `digest()`, add to the returned `DigestReport`:

```python
pipeline_stages=list(self._pipeline_stages),
```

**Step 6: Run tests**

```bash
uv run pytest tests/test_pipeline_metrics.py tests/test_watcher_pipeline.py -v
```
Expected: All pass

**Step 7: Run full suite**

```bash
uv run pytest 2>&1 | tail -3
```
Expected: All pass, no regressions

**Step 8: Commit**

```bash
git add src/neuro_mcp/service.py src/neuro_mcp/models.py tests/test_pipeline_metrics.py
git commit -m "feat: record and surface pipeline stage metrics in digest()"
```

---

### Task 6: Update tasks.md with new TASK-pipeline-metrics entry

**Files:**
- Modify: `3-code/tasks.md`

**Step 1: Add task rows for the new requirement**

In the Core Engine task table, after the Phase 3 tasks, add:

```
| TASK-pipeline-metrics-model | Add PipelineStageResult model | P2 | Done | [REQ-OBS-pipeline-metrics](...) | - | 2026-04-10 | From review S-1/S-2 follow-up |
| TASK-pipeline-metrics-record | Record stage metrics in refresh() and expose via digest() | P2 | Done | [REQ-OBS-pipeline-metrics](...) | TASK-pipeline-metrics-model | 2026-04-10 | |
```

Update the CLAUDE.md progress counter accordingly.

**Step 2: Commit**

```bash
git add 3-code/tasks.md CLAUDE.md
git commit -m "chore: add pipeline metrics tasks to tracker"
```

---

## Summary

| Task | Type | Time |
|------|------|------|
| 1. S-1 comments | Docs | 2 min |
| 2. S-2 startup log | Feat | 2 min |
| 3. REQ-OBS-pipeline-metrics | Spec | 5 min |
| 4. PipelineStageResult model | Feat | 5 min |
| 5. Record + surface metrics | Feat | 15 min |
| 6. tasks.md update | Admin | 2 min |

**Total: ~30 min of focused work, 6 small commits.**

All tasks are append-only / backwards-compatible. Existing tests should continue to pass.
