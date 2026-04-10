"""Test that get_note and scan_brain use the same type-based decay defaults."""
from neuro_mcp.freshness import TYPE_DEFAULT_DECAY, decay_days_for


def test_inbox_gets_7d_default():
    assert decay_days_for("inbox", None) == 7


def test_bug_gets_14d_default():
    assert decay_days_for("bug", None) == 14


def test_architecture_gets_90d_default():
    assert decay_days_for("architecture", None) == 90


def test_adr_gets_immutable():
    assert decay_days_for("adr", None) is None  # immutable = no decay


def test_unknown_type_gets_30d_default():
    assert decay_days_for("unknown-type", None) == 30


def test_explicit_decay_class_overrides_type_default():
    assert decay_days_for("inbox", "90d") == 90
