"""Security tests for get_note path handling."""
from __future__ import annotations

from pathlib import Path
from neuro_mcp.config import Settings
from neuro_mcp.service import NeuroMCPService


def test_get_note_rejects_path_traversal(tmp_path: Path):
    brain = tmp_path / "brain"
    brain.mkdir()
    code = tmp_path / "code"
    code.mkdir()
    settings = Settings(brain_root=brain, code_root=code, data_dir=tmp_path / "data")
    svc = NeuroMCPService(settings)
    result = svc.get_note("../../../etc/passwd")
    assert result["found"] is False
    assert "traversal" in result.get("error", "").lower() or "outside" in result.get("error", "").lower()


def test_get_note_allows_valid_path(tmp_path: Path):
    brain = tmp_path / "brain"
    brain.mkdir()
    code = tmp_path / "code"
    code.mkdir()
    note = brain / "test.md"
    note.write_text("---\ntitle: test\n---\nhello", encoding="utf-8")
    settings = Settings(brain_root=brain, code_root=code, data_dir=tmp_path / "data")
    svc = NeuroMCPService(settings)
    result = svc.get_note("test.md")
    assert result["found"] is True
