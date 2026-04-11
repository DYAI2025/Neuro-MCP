"""Test auto-frontmatter enrichment wired into the refresh() pipeline."""
import tempfile
from pathlib import Path

from neuro_mcp.config import Settings
from neuro_mcp.frontmatter import parse_markdown_note
from neuro_mcp.service import NeuroMCPService


def _settings(td: Path, **overrides) -> Settings:
    brain = td / "brain"
    code = td / "code"
    brain.mkdir(exist_ok=True)
    code.mkdir(exist_ok=True)
    return Settings(brain_root=brain, code_root=code, data_dir=td / "data", **overrides)


def _write_note(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_pipeline_enriches_bare_note_with_folder_rule():
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        brain = tdp / "brain"
        brain.mkdir()
        note = brain / "00-inbox" / "new-note.md"
        _write_note(note, "No frontmatter here.\n")

        settings = _settings(
            tdp,
            enable_auto_enrich_frontmatter=True,
            folder_type_map={
                "00-inbox": {"type": "inbox", "decay_class": "7d"},
            },
        )
        svc = NeuroMCPService(settings)
        svc.refresh()

        meta, _ = parse_markdown_note(note)
        assert meta["type"] == "inbox"
        assert meta["decay_class"] == "7d"
        assert meta["status"] == "active"
        assert meta["_neuro_mcp_enriched"] == "v1"


def test_pipeline_disabled_does_not_enrich():
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        brain = tdp / "brain"
        brain.mkdir()
        note = brain / "bare.md"
        _write_note(note, "Bare note.\n")

        settings = _settings(tdp, enable_auto_enrich_frontmatter=False)
        svc = NeuroMCPService(settings)
        svc.refresh()

        assert note.read_text(encoding="utf-8") == "Bare note.\n"


def test_pipeline_defaults_to_disabled():
    """Backwards compat: existing configs get no surprise mutations."""
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        brain = tdp / "brain"
        brain.mkdir()
        note = brain / "bare.md"
        _write_note(note, "Bare note.\n")

        settings = _settings(tdp)  # no overrides
        assert settings.enable_auto_enrich_frontmatter is False
        svc = NeuroMCPService(settings)
        svc.refresh()

        assert note.read_text(encoding="utf-8") == "Bare note.\n"


def test_pipeline_enriches_without_matching_rule():
    """Orphan notes get type: note, decay_class: 30d defaults."""
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        brain = tdp / "brain"
        brain.mkdir()
        note = brain / "random" / "orphan.md"
        _write_note(note, "Orphan.\n")

        settings = _settings(
            tdp,
            enable_auto_enrich_frontmatter=True,
            folder_type_map={"04-projekte": {"type": "note", "decay_class": "30d"}},
        )
        svc = NeuroMCPService(settings)
        svc.refresh()

        meta, _ = parse_markdown_note(note)
        assert meta["type"] == "note"
        assert meta["decay_class"] == "30d"
        assert meta["_neuro_mcp_enriched"] == "v1"


def test_pipeline_preserves_existing_user_fields():
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        brain = tdp / "brain"
        brain.mkdir()
        note = brain / "00-inbox" / "user.md"
        _write_note(
            note,
            "---\ntitle: My Title\ntype: custom\n---\n\nBody\n",
        )

        settings = _settings(
            tdp,
            enable_auto_enrich_frontmatter=True,
            folder_type_map={
                "00-inbox": {"type": "inbox", "decay_class": "7d"},
            },
        )
        svc = NeuroMCPService(settings)
        svc.refresh()

        meta, _ = parse_markdown_note(note)
        assert meta["title"] == "My Title"
        assert meta["type"] == "custom"  # not overwritten
        assert meta["decay_class"] == "7d"  # filled in


def test_pipeline_stage_metric_recorded():
    """Enrichment stage appears in digest pipeline_stages."""
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        brain = tdp / "brain"
        brain.mkdir()
        _write_note(brain / "n.md", "body\n")

        settings = _settings(tdp, enable_auto_enrich_frontmatter=True)
        svc = NeuroMCPService(settings)
        svc.refresh()
        digest = svc.digest()

        stage_names = {s.stage for s in digest.pipeline_stages}
        assert "enrich_frontmatter" in stage_names


def test_stc_sees_enriched_inbox_notes():
    """Pipeline ordering: enrich runs before STC, so bare notes in 00-inbox
    get type:inbox, decay_class:7d BEFORE STC evaluates them for promotion."""
    import subprocess
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        brain = tdp / "brain"
        code = tdp / "code"
        brain.mkdir()
        code.mkdir()
        # Git-init code so changed_files_since has something to read
        subprocess.run(["git", "init", "-q"], cwd=code, check=True)
        (code / "src").mkdir()
        src_file = code / "src" / "auth.py"
        src_file.write_text("def login(): pass\n")
        subprocess.run(["git", "add", "."], cwd=code, check=True)
        subprocess.run(
            ["git", "-c", "user.email=t@t.io", "-c", "user.name=t", "commit", "-qm", "init"],
            cwd=code, check=True,
        )

        # Bare note in 00-inbox with linked_paths pointing at the just-changed file
        inbox_note = brain / "00-inbox" / "auth-note.md"
        inbox_note.parent.mkdir()
        inbox_note.write_text(
            "---\nlinked_paths: [src/auth.py]\n---\nFresh auth notes.\n"
        )

        settings = _settings(
            tdp,
            enable_auto_enrich_frontmatter=True,
            enable_stc=True,
            folder_type_map={
                "00-inbox": {"type": "inbox", "decay_class": "7d"},
            },
        )
        svc = NeuroMCPService(settings)
        svc.refresh()

        # After refresh, note should be enriched (type:inbox, decay:7d) AND
        # STC stage should have run without errors (even if no promotion happens)
        meta, _ = parse_markdown_note(inbox_note)
        assert meta["type"] == "inbox"
        assert meta["decay_class"] == "7d"

        digest = svc.digest()
        stc_stage = next((s for s in digest.pipeline_stages if s.stage == "stc"), None)
        assert stc_stage is not None
        assert stc_stage.error_count == 0
