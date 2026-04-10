"""Test folder_type_map config field and folder → type resolution."""
import tempfile
from pathlib import Path

import pytest

from neuro_mcp.config import FolderTypeRule, Settings


def _settings(**overrides) -> Settings:
    with tempfile.TemporaryDirectory() as td:
        return Settings(brain_root=Path(td), code_root=Path(td), **overrides)


def test_folder_type_map_defaults_empty():
    s = _settings()
    assert s.folder_type_map == {}


def test_folder_type_map_accepts_dict_config():
    s = _settings(folder_type_map={
        "00-inbox": {"type": "inbox", "decay_class": "7d"},
        "04-projekte": {"type": "note", "decay_class": "30d"},
        "20-decisions": {"type": "adr", "decay_class": "immutable"},
    })
    assert len(s.folder_type_map) == 3
    inbox_rule = s.folder_type_map["00-inbox"]
    assert isinstance(inbox_rule, FolderTypeRule)
    assert inbox_rule.type == "inbox"
    assert inbox_rule.decay_class == "7d"


def test_folder_type_map_decay_class_defaults_to_30d():
    s = _settings(folder_type_map={
        "my-notes": {"type": "note"},
    })
    assert s.folder_type_map["my-notes"].decay_class == "30d"


def test_folder_type_map_rejects_missing_type():
    with pytest.raises(ValueError):
        _settings(folder_type_map={
            "broken": {"decay_class": "7d"},
        })


def test_folder_type_map_rejects_invalid_decay_class():
    with pytest.raises(ValueError):
        _settings(folder_type_map={
            "broken": {"type": "note", "decay_class": "3d"},
        })


def test_resolve_folder_type_matches_longest_prefix():
    """Longer folder prefixes win over shorter ones."""
    s = _settings(folder_type_map={
        "04-projekte": {"type": "note", "decay_class": "30d"},
        "04-projekte/critical": {"type": "architecture", "decay_class": "90d"},
    })
    rule_shallow = s.resolve_folder_type("04-projekte/notes/random.md")
    rule_deep = s.resolve_folder_type("04-projekte/critical/core-spec.md")
    assert rule_shallow.type == "note"
    assert rule_deep.type == "architecture"


def test_resolve_folder_type_returns_none_for_unmapped():
    s = _settings(folder_type_map={"04-projekte": {"type": "note"}})
    rule = s.resolve_folder_type("random-folder/note.md")
    assert rule is None


def test_resolve_folder_type_handles_empty_map():
    s = _settings()
    assert s.resolve_folder_type("anything.md") is None
