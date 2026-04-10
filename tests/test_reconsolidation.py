from __future__ import annotations

from pathlib import Path

from neuro_mcp.reconsolidation import apply_reconsolidation


def test_apply_reconsolidation_marks_labile(tmp_path: Path):
    note_path = tmp_path / "note.md"
    note_path.write_text(
        "---\ntitle: Old Stack\ntype: component\nstatus: active\n"
        "decay_class: 30d\nsource_precision: 0.8\nlast_verified: 2026-04-10\n---\n\n"
        "# Old Stack\n\nWe use Prisma ORM.\n"
    )
    contradictions = ["Note 'Old Stack' claims dependencies missing from manifests: prisma"]

    result = apply_reconsolidation(
        note_path=note_path,
        contradictions=contradictions,
    )
    assert result["action"] == "marked_labile"

    from neuro_mcp.frontmatter import parse_markdown_note
    meta, _ = parse_markdown_note(note_path)
    assert meta["status"] == "labile"
    assert "labile_since" in meta
    assert "labile_reasons" in meta


def test_apply_reconsolidation_skips_immutable(tmp_path: Path):
    note_path = tmp_path / "adr.md"
    note_path.write_text(
        "---\ntitle: ADR-001\ntype: adr\nstatus: accepted\n"
        "decay_class: immutable\nsource_precision: 0.95\n---\n\n"
        "# ADR-001\n\nDecision.\n"
    )
    result = apply_reconsolidation(
        note_path=note_path,
        contradictions=["Some contradiction"],
    )
    assert result["action"] == "skipped"
    assert "immutable" in result["reason"]


def test_apply_reconsolidation_skips_adr_type(tmp_path: Path):
    note_path = tmp_path / "adr2.md"
    note_path.write_text(
        "---\ntitle: ADR-002\ntype: adr\nstatus: accepted\n"
        "decay_class: 90d\nsource_precision: 0.9\n---\n\n"
        "# ADR-002\n\nAnother decision.\n"
    )
    result = apply_reconsolidation(
        note_path=note_path,
        contradictions=["Contradiction"],
    )
    assert result["action"] == "skipped"


def test_apply_reconsolidation_no_contradictions(tmp_path: Path):
    note_path = tmp_path / "ok.md"
    note_path.write_text(
        "---\ntitle: Fine\ntype: component\nstatus: active\n---\n\n# Fine\n\nAll good.\n"
    )
    result = apply_reconsolidation(note_path=note_path, contradictions=[])
    assert result["action"] == "no_action"


def test_apply_reconsolidation_file_not_found(tmp_path: Path):
    result = apply_reconsolidation(
        note_path=tmp_path / "nope.md",
        contradictions=["x"],
    )
    assert result["action"] == "skipped"
    assert "file_not_found" in result["reason"]
