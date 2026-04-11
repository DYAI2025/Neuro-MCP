"""Test auto-enrichment of note frontmatter based on folder rules."""
import tempfile
from datetime import date
from pathlib import Path

from neuro_mcp.config import FolderTypeRule
from neuro_mcp.frontmatter import enrich_note_frontmatter, parse_markdown_note


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_note_without_frontmatter_gets_full_frontmatter():
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        note = tdp / "my-note.md"
        _write(note, "Just a body with no frontmatter.\n")

        rule = FolderTypeRule(type="inbox", decay_class="7d")
        changed = enrich_note_frontmatter(note, rule=rule, today=date(2026, 4, 10))

        assert changed is True
        meta, body = parse_markdown_note(note)
        assert meta["type"] == "inbox"
        assert meta["decay_class"] == "7d"
        assert meta["status"] == "active"
        assert meta["last_verified"] == "2026-04-10"
        assert meta["created"] == "2026-04-10"
        assert meta["title"] == "My Note"
        assert meta["_neuro_mcp_enriched"] == "v1"
        assert "_neuro_mcp_last" in meta
        assert body.strip() == "Just a body with no frontmatter."


def test_note_with_partial_frontmatter_gets_missing_fields_only():
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        note = tdp / "existing.md"
        _write(
            note,
            "---\ntitle: Custom Title\ntype: architecture\n---\n\nBody content.\n",
        )

        rule = FolderTypeRule(type="inbox", decay_class="7d")
        changed = enrich_note_frontmatter(note, rule=rule, today=date(2026, 4, 10))

        assert changed is True
        meta, _ = parse_markdown_note(note)
        assert meta["title"] == "Custom Title"
        assert meta["type"] == "architecture"
        assert meta["decay_class"] == "7d"
        assert meta["status"] == "active"
        assert meta["last_verified"] == "2026-04-10"
        assert meta["_neuro_mcp_enriched"] == "v1"


def test_complete_frontmatter_not_modified():
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        note = tdp / "complete.md"
        original_content = (
            "---\n"
            "title: Complete Note\n"
            "type: note\n"
            "status: active\n"
            "decay_class: 30d\n"
            "last_verified: 2025-01-01\n"
            "created: 2025-01-01\n"
            "---\n\n"
            "Body.\n"
        )
        _write(note, original_content)

        rule = FolderTypeRule(type="inbox", decay_class="7d")
        changed = enrich_note_frontmatter(note, rule=rule, today=date(2026, 4, 10))

        assert changed is False
        assert note.read_text(encoding="utf-8") == original_content


def test_no_rule_uses_defaults():
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        note = tdp / "orphan.md"
        _write(note, "Orphan content.\n")

        changed = enrich_note_frontmatter(note, rule=None, today=date(2026, 4, 10))

        assert changed is True
        meta, _ = parse_markdown_note(note)
        assert meta["type"] == "note"
        assert meta["decay_class"] == "30d"
        assert meta["status"] == "active"
        assert meta["_neuro_mcp_enriched"] == "v1"


def test_existing_fields_never_overwritten():
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        note = tdp / "user-edited.md"
        _write(
            note,
            "---\ntitle: User Title\ntype: custom-type\ndecay_class: 60d\nstatus: labile\nlast_verified: 2020-05-05\ncreated: 2019-01-01\ntags: [important]\n---\n\nUser wrote this.\n",
        )

        rule = FolderTypeRule(type="inbox", decay_class="7d")
        changed = enrich_note_frontmatter(note, rule=rule, today=date(2026, 4, 10))

        assert changed is False
        meta, _ = parse_markdown_note(note)
        assert meta["title"] == "User Title"
        assert meta["type"] == "custom-type"
        assert meta["decay_class"] == "60d"
        assert meta["status"] == "labile"
        assert meta["last_verified"] == date(2020, 5, 5)
        assert meta["created"] == date(2019, 1, 1)
        assert meta["tags"] == ["important"]


def test_marker_updates_on_second_enrichment_pass():
    """After initial enrichment, if nothing else needs to change, no update."""
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        note = tdp / "note.md"
        _write(note, "Body\n")

        # First pass
        changed1 = enrich_note_frontmatter(note, rule=None, today=date(2026, 4, 10))
        assert changed1 is True
        meta_after_first, _ = parse_markdown_note(note)
        first_marker = meta_after_first["_neuro_mcp_last"]

        # Second pass — fully enriched, should not modify anything
        changed2 = enrich_note_frontmatter(note, rule=None, today=date(2026, 4, 10))
        assert changed2 is False
        meta_after_second, _ = parse_markdown_note(note)
        assert meta_after_second["_neuro_mcp_last"] == first_marker


def test_body_content_never_modified():
    """DEC-two-stage-mutations: body content must never be touched."""
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        note = tdp / "essay.md"
        body_content = (
            "# My Deep Thoughts\n\n"
            "This is a carefully worded essay.\n"
            "It contains poetry and **formatting**.\n\n"
            "- Bullet 1\n"
            "- Bullet 2\n"
        )
        _write(note, body_content)

        enrich_note_frontmatter(note, rule=None, today=date(2026, 4, 10))

        _, body = parse_markdown_note(note)
        assert body.strip() == body_content.strip()
