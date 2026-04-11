"""Test writing bidirectional related_notes frontmatter from wiki-link candidates."""
import tempfile
from pathlib import Path

from neuro_mcp.frontmatter import dump_markdown_note, parse_markdown_note
from neuro_mcp.wiki_links import WikiLinkCandidate, write_wiki_links


def _write_note(path: Path, meta: dict, body: str = "Body content.") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dump_markdown_note(meta, body), encoding="utf-8")


def test_writes_bidirectional_links():
    """Candidate (a, b) → both a.md gets [[b.md]] and b.md gets [[a.md]]."""
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        brain = tdp / "brain"
        a = brain / "alpha.md"
        b = brain / "beta.md"
        _write_note(a, {"title": "Alpha"})
        _write_note(b, {"title": "Beta"})

        candidates = [
            WikiLinkCandidate(
                source_owner_id="a",
                target_owner_id="b",
                source_path=str(a),
                target_path=str(b),
                similarity=0.9,
            )
        ]
        written = write_wiki_links(candidates, brain_root=brain)

        meta_a, _ = parse_markdown_note(a)
        meta_b, _ = parse_markdown_note(b)
        assert "[[beta]]" in meta_a["related_notes"]
        assert "[[alpha]]" in meta_b["related_notes"]
        assert set(written) == {str(a), str(b)}


def test_preserves_manual_entries():
    """Existing user-written entries in related_notes must not be removed."""
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        brain = tdp / "brain"
        a = brain / "a.md"
        b = brain / "b.md"
        _write_note(a, {"title": "A", "related_notes": ["[[manual-link]]"]})
        _write_note(b, {"title": "B"})

        candidates = [
            WikiLinkCandidate(
                source_owner_id="a",
                target_owner_id="b",
                source_path=str(a),
                target_path=str(b),
                similarity=0.85,
            )
        ]
        write_wiki_links(candidates, brain_root=brain)

        meta_a, _ = parse_markdown_note(a)
        assert "[[manual-link]]" in meta_a["related_notes"]
        assert "[[b]]" in meta_a["related_notes"]


def test_no_duplicate_links():
    """Running the writer twice must not duplicate existing auto-generated links."""
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        brain = tdp / "brain"
        a = brain / "a.md"
        b = brain / "b.md"
        _write_note(a, {"title": "A"})
        _write_note(b, {"title": "B"})

        candidates = [
            WikiLinkCandidate(
                source_owner_id="a",
                target_owner_id="b",
                source_path=str(a),
                target_path=str(b),
                similarity=0.9,
            )
        ]
        write_wiki_links(candidates, brain_root=brain)
        write_wiki_links(candidates, brain_root=brain)

        meta_a, _ = parse_markdown_note(a)
        assert meta_a["related_notes"].count("[[b]]") == 1


def test_stamps_enrichment_marker():
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        brain = tdp / "brain"
        a = brain / "a.md"
        b = brain / "b.md"
        _write_note(a, {"title": "A"})
        _write_note(b, {"title": "B"})

        candidates = [
            WikiLinkCandidate(
                source_owner_id="a",
                target_owner_id="b",
                source_path=str(a),
                target_path=str(b),
                similarity=0.9,
            )
        ]
        write_wiki_links(candidates, brain_root=brain)

        meta_a, _ = parse_markdown_note(a)
        assert meta_a["_neuro_mcp_enriched"] == "v1"
        assert "_neuro_mcp_last" in meta_a


def test_body_content_never_modified():
    """DEC-two-stage-mutations: body must never be touched."""
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        brain = tdp / "brain"
        a = brain / "a.md"
        b = brain / "b.md"
        body_a = "# A's essay\n\nCarefully written content.\n"
        body_b = "# B's notes\n\nMore content.\n"
        a.parent.mkdir(parents=True, exist_ok=True)
        a.write_text(dump_markdown_note({"title": "A"}, body_a), encoding="utf-8")
        b.write_text(dump_markdown_note({"title": "B"}, body_b), encoding="utf-8")

        candidates = [
            WikiLinkCandidate(
                source_owner_id="a",
                target_owner_id="b",
                source_path=str(a),
                target_path=str(b),
                similarity=0.9,
            )
        ]
        write_wiki_links(candidates, brain_root=brain)

        _, out_a = parse_markdown_note(a)
        _, out_b = parse_markdown_note(b)
        assert out_a.strip() == body_a.strip()
        assert out_b.strip() == body_b.strip()


def test_wiki_link_uses_relative_path_stem():
    """Wiki-link format uses the note stem (no directory, no .md), Obsidian-style."""
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        brain = tdp / "brain"
        a = brain / "04-projekte" / "my-project.md"
        b = brain / "10-architecture" / "diagram.md"
        _write_note(a, {"title": "Project"})
        _write_note(b, {"title": "Diagram"})

        candidates = [
            WikiLinkCandidate(
                source_owner_id="a",
                target_owner_id="b",
                source_path=str(a),
                target_path=str(b),
                similarity=0.9,
            )
        ]
        write_wiki_links(candidates, brain_root=brain)

        meta_a, _ = parse_markdown_note(a)
        assert "[[diagram]]" in meta_a["related_notes"]


def test_empty_candidates_noop():
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        brain = tdp / "brain"
        brain.mkdir()
        written = write_wiki_links([], brain_root=brain)
        assert written == []


def test_missing_file_skipped_gracefully():
    """If a candidate references a file that doesn't exist, skip it without raising."""
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        brain = tdp / "brain"
        brain.mkdir()
        existing = brain / "exists.md"
        _write_note(existing, {"title": "E"})

        candidates = [
            WikiLinkCandidate(
                source_owner_id="x",
                target_owner_id="y",
                source_path=str(brain / "missing-a.md"),
                target_path=str(brain / "missing-b.md"),
                similarity=0.9,
            )
        ]
        written = write_wiki_links(candidates, brain_root=brain)
        assert written == []
