from __future__ import annotations

from pathlib import Path

from neuro_mcp.config import Settings
from neuro_mcp.service import NeuroMCPService


def _vault_with_overlap(tmp_path: Path) -> Path:
    brain = tmp_path / "brain"
    arch = brain / "10-architecture"
    arch.mkdir(parents=True)
    (arch / "overview-v1.md").write_text(
        "---\ntitle: System Overview V1\ntype: architecture-doc\ndecay_class: 90d\n"
        "source_precision: 0.9\nlast_verified: 2026-04-10\n---\n\n"
        "# System Overview V1\n\nBazodiac uses RingStory as the central bridge object.\n"
    )
    (arch / "overview-v2.md").write_text(
        "---\ntitle: System Overview V2\ntype: architecture-doc\ndecay_class: 90d\n"
        "source_precision: 0.85\nlast_verified: 2026-04-10\n---\n\n"
        "# System Overview V2\n\nBazodiac uses RingStory as the central bridge object for profiles.\n"
    )
    return brain


def test_check_interference_returns_structure(tmp_path: Path):
    brain = _vault_with_overlap(tmp_path)
    code = tmp_path / "code"
    code.mkdir()
    svc = NeuroMCPService(Settings(
        brain_root=str(brain), code_root=str(code),
        data_dir=str(tmp_path / "data"), semantic_model=None,
    ))
    svc.refresh()
    result = svc.check_interference()
    assert isinstance(result, dict)
    assert "candidates" in result
    assert isinstance(result["candidates"], list)
    assert "threshold" in result
    assert "total_docs" in result
    assert result["total_docs"] > 0


def test_check_interference_empty_brain(tmp_path: Path):
    brain = tmp_path / "brain"
    brain.mkdir()
    code = tmp_path / "code"
    code.mkdir()
    svc = NeuroMCPService(Settings(
        brain_root=str(brain), code_root=str(code),
        data_dir=str(tmp_path / "data"), semantic_model=None,
    ))
    svc.refresh()
    result = svc.check_interference()
    assert result["candidates"] == []
    assert result["total_docs"] == 0
