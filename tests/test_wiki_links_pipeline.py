"""Test wiki-links pipeline stage wired into refresh()."""
import tempfile
from pathlib import Path

from neuro_mcp.config import Settings
from neuro_mcp.frontmatter import dump_markdown_note, parse_markdown_note
from neuro_mcp.service import NeuroMCPService


def _write_note(path: Path, meta: dict, body: str = "Body content.") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dump_markdown_note(meta, body), encoding="utf-8")


def _settings(td: Path, **overrides) -> Settings:
    brain = td / "brain"
    code = td / "code"
    brain.mkdir(exist_ok=True)
    code.mkdir(exist_ok=True)
    return Settings(brain_root=brain, code_root=code, data_dir=td / "data", **overrides)


def test_pipeline_enabled_writes_bidirectional_links():
    """With enable_auto_wiki_links=true, similar notes get auto-linked."""
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        brain = tdp / "brain"
        brain.mkdir()
        a = brain / "a.md"
        b = brain / "b.md"
        _write_note(a, {"title": "A"}, "python async concurrency patterns for web")
        _write_note(b, {"title": "B"}, "python async concurrency patterns for apps")

        settings = _settings(
            tdp,
            enable_auto_wiki_links=True,
            auto_link_threshold=0.3,
        )
        svc = NeuroMCPService(settings)
        svc.refresh()

        meta_a, _ = parse_markdown_note(a)
        meta_b, _ = parse_markdown_note(b)
        assert meta_a.get("related_notes") is not None
        assert meta_b.get("related_notes") is not None
        assert "[[b]]" in meta_a["related_notes"]
        assert "[[a]]" in meta_b["related_notes"]


def test_pipeline_disabled_does_not_write_links():
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        brain = tdp / "brain"
        brain.mkdir()
        a = brain / "a.md"
        b = brain / "b.md"
        _write_note(a, {"title": "A"}, "identical content here")
        _write_note(b, {"title": "B"}, "identical content here")

        settings = _settings(tdp, enable_auto_wiki_links=False)
        svc = NeuroMCPService(settings)
        svc.refresh()

        meta_a, _ = parse_markdown_note(a)
        meta_b, _ = parse_markdown_note(b)
        assert meta_a.get("related_notes") is None
        assert meta_b.get("related_notes") is None


def test_pipeline_defaults_to_disabled():
    """Backwards compat: existing configs get no surprise link writes."""
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        brain = tdp / "brain"
        brain.mkdir()
        a = brain / "a.md"
        b = brain / "b.md"
        _write_note(a, {"title": "A"}, "identical content")
        _write_note(b, {"title": "B"}, "identical content")

        settings = _settings(tdp)  # no overrides
        assert settings.enable_auto_wiki_links is False
        svc = NeuroMCPService(settings)
        svc.refresh()

        meta_a, _ = parse_markdown_note(a)
        assert meta_a.get("related_notes") is None


def test_pipeline_respects_threshold():
    """Low-similarity notes should not get linked even when enabled."""
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        brain = tdp / "brain"
        brain.mkdir()
        a = brain / "a.md"
        b = brain / "b.md"
        _write_note(a, {"title": "A"}, "python async concurrency")
        _write_note(b, {"title": "B"}, "italian pasta recipes with tomatoes")

        settings = _settings(
            tdp,
            enable_auto_wiki_links=True,
            auto_link_threshold=0.8,
        )
        svc = NeuroMCPService(settings)
        svc.refresh()

        meta_a, _ = parse_markdown_note(a)
        meta_b, _ = parse_markdown_note(b)
        # Below threshold — no links
        assert meta_a.get("related_notes") is None or "[[b]]" not in meta_a.get("related_notes", [])


def test_pipeline_stage_metric_recorded():
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        brain = tdp / "brain"
        brain.mkdir()
        a = brain / "a.md"
        _write_note(a, {"title": "A"}, "body")

        settings = _settings(tdp, enable_auto_wiki_links=True)
        svc = NeuroMCPService(settings)
        svc.refresh()

        digest = svc.digest()
        stage_names = {s.stage for s in digest.pipeline_stages}
        assert "wiki_links" in stage_names


def test_pipeline_preserves_manual_related_notes():
    """Manual entries in related_notes survive the pipeline pass."""
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        brain = tdp / "brain"
        brain.mkdir()
        a = brain / "a.md"
        b = brain / "b.md"
        _write_note(
            a,
            {"title": "A", "related_notes": ["[[user-handcrafted-link]]"]},
            "python async concurrency",
        )
        _write_note(b, {"title": "B"}, "python async concurrency")

        settings = _settings(
            tdp,
            enable_auto_wiki_links=True,
            auto_link_threshold=0.3,
        )
        svc = NeuroMCPService(settings)
        svc.refresh()

        meta_a, _ = parse_markdown_note(a)
        assert "[[user-handcrafted-link]]" in meta_a["related_notes"]
        assert "[[b]]" in meta_a["related_notes"]
