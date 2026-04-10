from __future__ import annotations

from pathlib import Path

from neuro_mcp.config import Settings
from neuro_mcp.service import NeuroMCPService


def test_ingest_creates_new_note(tmp_path: Path):
    brain = tmp_path / "brain"
    brain.mkdir()
    code = tmp_path / "code"
    code.mkdir()
    svc = NeuroMCPService(Settings(
        brain_root=str(brain), code_root=str(code),
        data_dir=str(tmp_path / "data"), semantic_model=None,
    ))
    result = svc.ingest_note(
        relative_path="80-inbox/new-discovery.md",
        title="API Discovery",
        content="# API Discovery\n\nFound that the app uses GraphQL internally.",
        note_type="inbox",
        tags=["api", "discovery"],
        decay_class="7d",
        source_precision=0.7,
        claimed_dependencies=[],
    )
    assert result["status"] == "created"
    assert (brain / "80-inbox" / "new-discovery.md").exists()

    from neuro_mcp.frontmatter import parse_markdown_note
    meta, body = parse_markdown_note(brain / "80-inbox" / "new-discovery.md")
    assert meta["title"] == "API Discovery"
    assert meta["type"] == "inbox"
    assert meta["decay_class"] == "7d"
    assert "GraphQL" in body


def test_ingest_updates_existing_note(tmp_path: Path):
    brain = tmp_path / "brain"
    brain.mkdir()
    (brain / "note.md").write_text(
        "---\ntitle: Old Title\ntype: note\n---\n\n# Old\n\nOld content\n"
    )
    code = tmp_path / "code"
    code.mkdir()
    svc = NeuroMCPService(Settings(
        brain_root=str(brain), code_root=str(code),
        data_dir=str(tmp_path / "data"), semantic_model=None,
    ))
    result = svc.ingest_note(
        relative_path="note.md",
        title="New Title",
        content="# New\n\nUpdated content.",
        note_type="note",
        tags=["updated"],
        decay_class="30d",
        source_precision=0.8,
        claimed_dependencies=[],
    )
    assert result["status"] == "updated"

    from neuro_mcp.frontmatter import parse_markdown_note
    meta, body = parse_markdown_note(brain / "note.md")
    assert meta["title"] == "New Title"
    assert "Updated content" in body
