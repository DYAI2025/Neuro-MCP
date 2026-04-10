"""Test auto_mark_labile marks notes with missing linked files as labile."""
import tempfile
from pathlib import Path

from neuro_mcp.config import Settings
from neuro_mcp.frontmatter import dump_markdown_note, parse_markdown_note


def _make_note(brain_dir: Path, name: str, linked_paths: list[str]) -> Path:
    meta = {"title": name, "type": "note", "status": "active",
            "linked_paths": linked_paths, "decay_class": "30d"}
    p = brain_dir / f"{name}.md"
    p.write_text(dump_markdown_note(meta, f"Content of {name}"), encoding="utf-8")
    return p


def test_missing_linked_file_marks_labile():
    with tempfile.TemporaryDirectory() as td:
        brain = Path(td) / "brain"
        code = Path(td) / "code"
        brain.mkdir()
        code.mkdir()

        # Create note that links to a file that doesn't exist
        note_path = _make_note(brain, "test-note", ["src/missing.py"])

        settings = Settings(
            brain_root=brain, code_root=code,
            data_dir=Path(td) / "data",
            auto_mark_labile=True,
        )
        from neuro_mcp.service import NeuroMCPService
        svc = NeuroMCPService(settings)
        svc.refresh()

        meta, _ = parse_markdown_note(note_path)
        assert meta["status"] == "labile"
        assert any("missing" in r for r in meta.get("labile_reasons", []))


def test_existing_linked_file_stays_active():
    with tempfile.TemporaryDirectory() as td:
        brain = Path(td) / "brain"
        code = Path(td) / "code"
        brain.mkdir()
        code.mkdir()

        # Create the linked file
        (code / "src").mkdir()
        (code / "src" / "exists.py").write_text("pass")

        note_path = _make_note(brain, "test-note", ["src/exists.py"])

        settings = Settings(
            brain_root=brain, code_root=code,
            data_dir=Path(td) / "data",
            auto_mark_labile=True,
        )
        from neuro_mcp.service import NeuroMCPService
        svc = NeuroMCPService(settings)
        svc.refresh()

        meta, _ = parse_markdown_note(note_path)
        assert meta["status"] == "active"


def test_disabled_does_not_mark_labile():
    with tempfile.TemporaryDirectory() as td:
        brain = Path(td) / "brain"
        code = Path(td) / "code"
        brain.mkdir()
        code.mkdir()

        note_path = _make_note(brain, "test-note", ["src/missing.py"])

        settings = Settings(
            brain_root=brain, code_root=code,
            data_dir=Path(td) / "data",
            auto_mark_labile=False,  # disabled
        )
        from neuro_mcp.service import NeuroMCPService
        svc = NeuroMCPService(settings)
        svc.refresh()

        meta, _ = parse_markdown_note(note_path)
        assert meta["status"] == "active"  # unchanged
