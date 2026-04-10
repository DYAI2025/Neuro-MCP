"""Test that GC backups don't collide for same-named files in different dirs."""
from __future__ import annotations

from pathlib import Path
from neuro_mcp.models import GarbageCollectionItem
from neuro_mcp.gc import execute_gc_actions


def test_backup_preserves_both_files(tmp_path: Path):
    dir_a = tmp_path / "dir_a"
    dir_b = tmp_path / "dir_b"
    dir_a.mkdir()
    dir_b.mkdir()

    note_a = dir_a / "note.md"
    note_b = dir_b / "note.md"
    note_a.write_text("---\ntitle: A\n---\ncontent A")
    note_b.write_text("---\ntitle: B\n---\ncontent B")

    backup_dir = tmp_path / "backups"

    items = [
        GarbageCollectionItem(
            note_id="a", path=str(note_a), status_before="active",
            status_after="archived", action="archive", reason="test",
        ),
        GarbageCollectionItem(
            note_id="b", path=str(note_b), status_before="active",
            status_after="archived", action="archive", reason="test",
        ),
    ]

    results = execute_gc_actions(items, backup_dir=backup_dir)
    assert all(r["executed"] for r in results)

    backup_files = list(backup_dir.rglob("*.md"))
    assert len(backup_files) >= 2, f"Expected 2 backups, got {len(backup_files)}: {backup_files}"
