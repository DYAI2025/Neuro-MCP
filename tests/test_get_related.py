from __future__ import annotations

from pathlib import Path

from neuro_mcp.config import Settings
from neuro_mcp.service import NeuroMCPService


def _vault(tmp_path: Path) -> Path:
    brain = tmp_path / "brain"
    arch = brain / "10-architecture"
    arch.mkdir(parents=True)
    (arch / "system-overview.md").write_text(
        "---\ntitle: System Overview\ntype: architecture-doc\ndecay_class: 90d\n"
        "source_precision: 0.9\nlast_verified: 2026-04-10\n---\n\n"
        "# System Overview\n\nThe app uses RingStory as central bridge.\n"
    )
    (arch / "fusion-ring.md").write_text(
        "---\ntitle: Fusion Ring Concept\ntype: architecture-doc\ndecay_class: 90d\n"
        "source_precision: 0.85\nlast_verified: 2026-04-10\n---\n\n"
        "# Fusion Ring\n\nThe Fusion Ring maps signals to 12 sectors.\n"
    )
    inbox = brain / "80-inbox"
    inbox.mkdir()
    (inbox / "unrelated.md").write_text(
        "---\ntitle: Meeting Notes\ntype: inbox\ndecay_class: 7d\n"
        "source_precision: 0.3\nlast_verified: 2026-04-10\n---\n\n"
        "# Meeting Notes\n\nDiscussed lunch plans.\n"
    )
    return brain


def test_get_related_returns_results(tmp_path: Path):
    brain = _vault(tmp_path)
    code = tmp_path / "code"
    code.mkdir()
    svc = NeuroMCPService(Settings(
        brain_root=str(brain), code_root=str(code),
        data_dir=str(tmp_path / "data"), semantic_model=None,
    ))
    svc.refresh()
    result = svc.get_related("10-architecture/system-overview.md", top_k=2)
    assert result["found"] is True
    assert isinstance(result["related"], list)


def test_get_related_not_found(tmp_path: Path):
    brain = tmp_path / "brain"
    brain.mkdir()
    code = tmp_path / "code"
    code.mkdir()
    svc = NeuroMCPService(Settings(
        brain_root=str(brain), code_root=str(code),
        data_dir=str(tmp_path / "data"), semantic_model=None,
    ))
    result = svc.get_related("nope.md")
    assert result["found"] is False
