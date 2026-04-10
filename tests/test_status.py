from __future__ import annotations

from pathlib import Path

from neuro_mcp.config import Settings
from neuro_mcp.service import NeuroMCPService


def _vault(tmp_path: Path) -> Path:
    brain = tmp_path / "brain"
    arch = brain / "10-architecture"
    arch.mkdir(parents=True)
    (arch / "sys.md").write_text(
        "---\ntitle: Sys\ntype: architecture-doc\ndecay_class: 90d\n"
        "source_precision: 0.9\nlast_verified: 2026-04-10\n---\n\n# Sys\n\nContent.\n"
    )
    adr = brain / "20-decisions"
    adr.mkdir()
    (adr / "adr-001.md").write_text(
        "---\ntitle: ADR-001\ntype: adr\ndecay_class: immutable\n"
        "source_precision: 0.95\n---\n\n# ADR-001\n\nDecision.\n"
    )
    inbox = brain / "80-inbox"
    inbox.mkdir()
    (inbox / "quick.md").write_text(
        "---\ntitle: Quick\ntype: inbox\ndecay_class: 7d\n"
        "source_precision: 0.3\n---\n\n# Quick\n\nIdea.\n"
    )
    return brain


def test_status_returns_counts(tmp_path: Path):
    brain = _vault(tmp_path)
    code = tmp_path / "code"
    code.mkdir()
    svc = NeuroMCPService(Settings(
        brain_root=str(brain), code_root=str(code),
        data_dir=str(tmp_path / "data"), semantic_model=None,
    ))
    svc.refresh()
    result = svc.status()
    assert result["total_notes"] == 3
    assert isinstance(result["by_type"], dict)
    assert isinstance(result["by_freshness"], dict)
    assert isinstance(result["mode"], str)
    assert isinstance(result["recommendations"], list)
    assert isinstance(result["has_semantic"], bool)
