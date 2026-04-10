from __future__ import annotations

from pathlib import Path

from neuro_mcp.config import Settings
from neuro_mcp.service import NeuroMCPService


def _create_sample_vault(tmp_path: Path) -> Path:
    brain = tmp_path / "brain"
    arch = brain / "10-architecture"
    arch.mkdir(parents=True)
    (arch / "system-overview.md").write_text(
        "---\n"
        "title: System Overview\n"
        "type: architecture-doc\n"
        "status: active\n"
        "decay_class: 90d\n"
        "source_precision: 0.9\n"
        "last_verified: 2026-04-10\n"
        "tags: [architecture]\n"
        "---\n\n"
        "# System Overview\n\n"
        "Bazodiac uses RingStory as the central bridge.\n\n"
        "## Components\n\n"
        "Frontend: Next.js, Backend: Python\n"
    )
    return brain


def test_get_note_returns_content(tmp_path: Path):
    brain = _create_sample_vault(tmp_path)
    code = tmp_path / "code"
    code.mkdir()
    svc = NeuroMCPService(Settings(
        brain_root=str(brain), code_root=str(code),
        data_dir=str(tmp_path / "data"), semantic_model=None,
    ))
    result = svc.get_note("10-architecture/system-overview.md")
    assert result["found"] is True
    assert result["title"] == "System Overview"
    assert "RingStory" in result["content"]
    assert result["metadata"]["decay_class"] == "90d"
    assert result["metadata"]["freshness"] is not None


def test_get_note_not_found(tmp_path: Path):
    brain = tmp_path / "brain"
    brain.mkdir()
    code = tmp_path / "code"
    code.mkdir()
    svc = NeuroMCPService(Settings(
        brain_root=str(brain), code_root=str(code),
        data_dir=str(tmp_path / "data"), semantic_model=None,
    ))
    result = svc.get_note("nonexistent.md")
    assert result["found"] is False
