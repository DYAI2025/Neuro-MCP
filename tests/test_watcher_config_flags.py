"""Test watcher pipeline config flags exist and default to False."""
import tempfile
from pathlib import Path

from neuro_mcp.config import Settings


def _minimal_settings(**overrides):
    with tempfile.TemporaryDirectory() as td:
        brain = Path(td) / "brain"
        code = Path(td) / "code"
        brain.mkdir()
        code.mkdir()
        return Settings(brain_root=brain, code_root=code, **overrides)


def test_enable_stc_defaults_false():
    s = _minimal_settings()
    assert s.enable_stc is False


def test_enable_auto_labile_defaults_false():
    s = _minimal_settings()
    assert s.enable_auto_labile is False


def test_enable_auto_reconcile_defaults_false():
    s = _minimal_settings()
    assert s.enable_auto_reconcile is False


def test_flags_configurable():
    s = _minimal_settings(enable_stc=True, enable_auto_labile=True, enable_auto_reconcile=True)
    assert s.enable_stc is True
    assert s.enable_auto_labile is True
    assert s.enable_auto_reconcile is True


def test_existing_configs_unaffected():
    s = _minimal_settings()
    assert s.auto_watch is True
    assert s.auto_mark_labile is False
    assert s.watch_debounce_seconds == 5.0
