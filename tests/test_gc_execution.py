from __future__ import annotations

from pathlib import Path

from neuro_mcp.gc import execute_gc_actions
from neuro_mcp.models import GarbageCollectionItem


def test_execute_gc_updates_frontmatter(tmp_path: Path):
    note = tmp_path / "note.md"
    note.write_text(
        "---\ntitle: Old Bug\ntype: bug\nstatus: active\n---\n\n# Old Bug\n\nDetails.\n"
    )
    item = GarbageCollectionItem(
        note_id="x",
        path=str(note),
        action="archive",
        reason="stale",
        status_before="active",
        status_after="archived",
    )
    results = execute_gc_actions([item], backup_dir=tmp_path / "backups")
    assert results[0]["executed"] is True
    assert results[0]["status_after"] == "archived"

    from neuro_mcp.frontmatter import parse_markdown_note
    meta, _ = parse_markdown_note(note)
    assert meta["status"] == "archived"
    assert "archived_at" in meta

    # Backup exists
    assert (tmp_path / "backups").exists()
    assert (tmp_path / "backups" / "note.md").exists()


def test_execute_gc_file_not_found(tmp_path: Path):
    item = GarbageCollectionItem(
        note_id="y",
        path=str(tmp_path / "nope.md"),
        action="archive",
        reason="stale",
        status_before="active",
        status_after="archived",
    )
    results = execute_gc_actions([item])
    assert results[0]["executed"] is False
    assert "file_not_found" in results[0]["reason"]


def test_execute_gc_status_update(tmp_path: Path):
    note = tmp_path / "comp.md"
    note.write_text(
        "---\ntitle: Component\ntype: component\nstatus: active\n---\n\n# Component\n\nInfo.\n"
    )
    item = GarbageCollectionItem(
        note_id="z",
        path=str(note),
        action="update_status",
        reason="older_than_30d",
        status_before="active",
        status_after="stale",
    )
    results = execute_gc_actions([item])
    assert results[0]["executed"] is True

    from neuro_mcp.frontmatter import parse_markdown_note
    meta, _ = parse_markdown_note(note)
    assert meta["status"] == "stale"
    # Should NOT have archived_at since it's not archived
    assert "archived_at" not in meta
