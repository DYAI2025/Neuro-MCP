"""Test that gc --apply actually mutates frontmatter."""
import tempfile
from pathlib import Path

from neuro_mcp.frontmatter import dump_markdown_note, parse_markdown_note
from neuro_mcp.gc import execute_gc_actions
from neuro_mcp.models import GarbageCollectionItem


def _write_note(path: Path, status: str = "active", note_type: str = "inbox"):
    meta = {"title": "Test", "type": note_type, "status": status}
    path.write_text(dump_markdown_note(meta, "body"), encoding="utf-8")


def test_execute_gc_archives_note():
    with tempfile.TemporaryDirectory() as td:
        note_path = Path(td) / "test.md"
        _write_note(note_path, status="active", note_type="inbox")

        item = GarbageCollectionItem(
            note_id="test-1",
            path=str(note_path),
            action="archive",
            reason="stale inbox",
            status_before="active",
            status_after="archived",
        )
        results = execute_gc_actions([item])
        assert results[0]["executed"] is True

        meta, _ = parse_markdown_note(note_path)
        assert meta["status"] == "archived"
        assert "archived_at" in meta


def test_execute_gc_idempotent():
    with tempfile.TemporaryDirectory() as td:
        note_path = Path(td) / "test.md"
        _write_note(note_path, status="archived", note_type="inbox")

        item = GarbageCollectionItem(
            note_id="test-1",
            path=str(note_path),
            action="archive",
            reason="already archived",
            status_before="archived",
            status_after="archived",
        )
        results = execute_gc_actions([item])
        assert results[0]["executed"] is True

        meta, _ = parse_markdown_note(note_path)
        assert meta["status"] == "archived"


def test_execute_gc_missing_file():
    item = GarbageCollectionItem(
        note_id="test-1",
        path="/nonexistent/path.md",
        action="archive",
        reason="test",
        status_before="active",
        status_after="archived",
    )
    results = execute_gc_actions([item])
    assert results[0]["executed"] is False


def test_gc_dry_run_does_not_mutate():
    with tempfile.TemporaryDirectory() as td:
        note_path = Path(td) / "test.md"
        _write_note(note_path, status="active")

        # dry_run report should NOT trigger execute_gc_actions
        # This is tested by checking the file is unchanged after build_gc_report
        from neuro_mcp.gc import build_gc_report
        from neuro_mcp.models import Mode

        notes = [{"note_id": "t", "path": str(note_path), "note_type": "inbox",
                  "decay_class": "7d", "last_verified": None,
                  "source_files_exist": True, "status": "active"}]
        report = build_gc_report(notes, Mode.PHASIC, dry_run=True)

        meta, _ = parse_markdown_note(note_path)
        assert meta["status"] == "active"  # unchanged
