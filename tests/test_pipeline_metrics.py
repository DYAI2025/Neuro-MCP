"""Test PipelineStageResult model and metric recording."""
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


import tempfile
from pathlib import Path
from unittest.mock import patch

from neuro_mcp.config import Settings
from neuro_mcp.frontmatter import dump_markdown_note
from neuro_mcp.service import NeuroMCPService


def _make_note(brain_dir: Path, name: str) -> Path:
    meta = {"title": name, "type": "note", "status": "active", "decay_class": "30d"}
    p = brain_dir / f"{name}.md"
    p.write_text(dump_markdown_note(meta, f"Content of {name}"), encoding="utf-8")
    return p


def _settings(td: Path, **overrides) -> Settings:
    brain = td / "brain"
    code = td / "code"
    brain.mkdir(exist_ok=True)
    code.mkdir(exist_ok=True)
    return Settings(brain_root=brain, code_root=code, data_dir=td / "data", **overrides)


def test_refresh_records_pipeline_stage_metrics():
    """After refresh, service exposes per-stage metrics via digest()."""
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        brain = tdp / "brain"
        brain.mkdir(exist_ok=True)
        _make_note(brain, "n1")
        settings = _settings(tdp, enable_stc=True, enable_auto_reconcile=False)
        svc = NeuroMCPService(settings)
        svc.refresh()
        digest = svc.digest()

        stage_names = {s.stage for s in digest.pipeline_stages}
        assert "stc" in stage_names
        assert "labile" in stage_names
        assert "auto_reconcile" not in stage_names  # disabled

        for stage in digest.pipeline_stages:
            assert stage.duration_ms >= 0.0


def test_disabled_stage_not_in_metrics():
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        brain = tdp / "brain"
        brain.mkdir(exist_ok=True)
        _make_note(brain, "n1")
        settings = _settings(tdp, enable_stc=False, enable_auto_reconcile=False)
        svc = NeuroMCPService(settings)
        svc.refresh()
        digest = svc.digest()

        stage_names = {s.stage for s in digest.pipeline_stages}
        assert "stc" not in stage_names
        assert "labile" in stage_names  # labile always runs


def test_stage_error_counted():
    """If a stage raises, error_count is 1 but refresh still completes."""
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        brain = tdp / "brain"
        brain.mkdir(exist_ok=True)
        _make_note(brain, "n1")
        settings = _settings(tdp, enable_stc=True)
        svc = NeuroMCPService(settings)
        with patch.object(svc, "_run_stc_promotions", side_effect=RuntimeError("boom")):
            svc.refresh()
        digest = svc.digest()
        stc_stage = next((s for s in digest.pipeline_stages if s.stage == "stc"), None)
        assert stc_stage is not None
        assert stc_stage.error_count == 1
