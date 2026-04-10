"""Security tests for writer module."""
from __future__ import annotations

import pytest
from pathlib import Path
from neuro_mcp.writer import write_note


def test_write_note_rejects_path_traversal(tmp_path: Path):
    brain_root = tmp_path / "brain"
    brain_root.mkdir()
    with pytest.raises(ValueError, match="outside brain root"):
        write_note(brain_root, "../../../etc/evil.md", title="hack", content="pwned")


def test_write_note_rejects_absolute_path(tmp_path: Path):
    brain_root = tmp_path / "brain"
    brain_root.mkdir()
    with pytest.raises(ValueError, match="outside brain root"):
        write_note(brain_root, "/etc/passwd", title="hack", content="pwned")


def test_write_note_allows_valid_subpath(tmp_path: Path):
    brain_root = tmp_path / "brain"
    brain_root.mkdir()
    result = write_note(brain_root, "notes/valid.md", title="ok", content="fine")
    assert result["status"] == "created"
    assert (brain_root / "notes" / "valid.md").exists()
