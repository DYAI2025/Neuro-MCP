"""Test watcher pipeline orchestration: stages run, error isolation, flags gate stages."""
import tempfile
from pathlib import Path
from unittest.mock import patch

from neuro_mcp.config import Settings
from neuro_mcp.frontmatter import dump_markdown_note
from neuro_mcp.service import NeuroMCPService


def _make_note(brain_dir: Path, name: str, **meta_extra) -> Path:
    meta = {"title": name, "type": "note", "status": "active", "decay_class": "30d"}
    meta.update(meta_extra)
    p = brain_dir / f"{name}.md"
    p.write_text(dump_markdown_note(meta, f"Content of {name}"), encoding="utf-8")
    return p


def _settings(td: Path, **overrides) -> Settings:
    brain = td / "brain"
    code = td / "code"
    brain.mkdir(exist_ok=True)
    code.mkdir(exist_ok=True)
    return Settings(
        brain_root=brain,
        code_root=code,
        data_dir=td / "data",
        **overrides,
    )


def test_refresh_runs_all_enabled_stages():
    """With all flags enabled, refresh executes STC, labile, and auto-reconcile stages."""
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        settings = _settings(
            tdp,
            enable_stc=True,
            enable_auto_reconcile=True,
            auto_mark_labile=True,
        )
        _make_note(tdp / "brain", "note1")
        svc = NeuroMCPService(settings)

        with patch.object(svc, "_run_stc_promotions", wraps=svc._run_stc_promotions) as stc_mock, \
             patch.object(svc, "_check_labile_linked_paths", wraps=svc._check_labile_linked_paths) as lab_mock, \
             patch.object(svc, "_run_auto_reconcile", wraps=svc._run_auto_reconcile) as rec_mock:
            svc.refresh()
            assert stc_mock.called
            assert lab_mock.called
            assert rec_mock.called


def test_enable_stc_false_skips_stc_stage():
    """When enable_stc=False, STC stage is not invoked."""
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        settings = _settings(tdp, enable_stc=False)
        _make_note(tdp / "brain", "note1")
        svc = NeuroMCPService(settings)

        with patch.object(svc, "_run_stc_promotions") as stc_mock:
            svc.refresh()
            assert not stc_mock.called


def test_enable_auto_reconcile_false_skips_reconcile_stage():
    """When enable_auto_reconcile=False (default), reconcile stage is skipped."""
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        settings = _settings(tdp)  # defaults
        _make_note(tdp / "brain", "note1")
        svc = NeuroMCPService(settings)

        with patch.object(svc, "_run_auto_reconcile") as rec_mock:
            svc.refresh()
            assert not rec_mock.called


def test_stc_stage_error_does_not_block_labile():
    """If STC raises, labile stage still runs."""
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        settings = _settings(tdp, enable_stc=True, auto_mark_labile=True)
        _make_note(tdp / "brain", "note1")
        svc = NeuroMCPService(settings)

        with patch.object(svc, "_run_stc_promotions", side_effect=RuntimeError("STC boom")), \
             patch.object(svc, "_check_labile_linked_paths") as lab_mock:
            svc.refresh()  # should not raise
            assert lab_mock.called


def test_labile_stage_error_does_not_block_reconcile():
    """If labile raises, reconcile stage still runs."""
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        settings = _settings(tdp, enable_stc=True, enable_auto_reconcile=True)
        _make_note(tdp / "brain", "note1")
        svc = NeuroMCPService(settings)

        with patch.object(svc, "_check_labile_linked_paths", side_effect=RuntimeError("labile boom")), \
             patch.object(svc, "_run_auto_reconcile") as rec_mock:
            svc.refresh()  # should not raise
            assert rec_mock.called


def test_refresh_completes_even_if_all_pipeline_stages_fail():
    """Pipeline stage failures never prevent refresh from completing."""
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        settings = _settings(tdp, enable_stc=True, enable_auto_reconcile=True)
        _make_note(tdp / "brain", "note1")
        svc = NeuroMCPService(settings)

        with patch.object(svc, "_run_stc_promotions", side_effect=RuntimeError("stc")), \
             patch.object(svc, "_check_labile_linked_paths", side_effect=RuntimeError("labile")), \
             patch.object(svc, "_run_auto_reconcile", side_effect=RuntimeError("reconcile")):
            svc.refresh()  # must not raise
            assert svc._loaded is True
