"""Test auto_link_threshold config field for wiki-link generation."""
import tempfile
from pathlib import Path

import pytest
from pydantic import ValidationError

from neuro_mcp.config import Settings


def _settings(**overrides) -> Settings:
    with tempfile.TemporaryDirectory() as td:
        return Settings(brain_root=Path(td), code_root=Path(td), **overrides)


def test_auto_link_threshold_defaults_to_0_8():
    """Default 0.8 — stricter than TF-IDF literature (0.7) so only highly
    confident matches become wiki-links. Must remain below
    similarity_threshold (0.85) used by check_interference."""
    s = _settings()
    assert s.auto_link_threshold == 0.8


def test_auto_link_threshold_below_interference_threshold():
    """Wiki-link threshold must be <= interference threshold — otherwise
    link generation would fire on pairs that are also duplicates, and the
    interference resolver would clean them up immediately."""
    s = _settings()
    assert s.auto_link_threshold <= s.similarity_threshold


def test_auto_link_threshold_configurable():
    s = _settings(auto_link_threshold=0.85)
    assert s.auto_link_threshold == 0.85


def test_auto_link_threshold_rejects_below_zero():
    with pytest.raises(ValidationError):
        _settings(auto_link_threshold=-0.1)


def test_auto_link_threshold_rejects_above_one():
    with pytest.raises(ValidationError):
        _settings(auto_link_threshold=1.5)


def test_auto_link_threshold_accepts_boundary_values():
    s_low = _settings(auto_link_threshold=0.0)
    assert s_low.auto_link_threshold == 0.0
    s_high = _settings(auto_link_threshold=1.0)
    assert s_high.auto_link_threshold == 1.0


def test_auto_link_threshold_accepts_near_zero():
    """Values just above the lower bound should be accepted."""
    s = _settings(auto_link_threshold=0.01)
    assert s.auto_link_threshold == 0.01


def test_auto_link_threshold_accepts_near_one():
    """Values just below the upper bound should be accepted."""
    s = _settings(auto_link_threshold=0.99)
    assert s.auto_link_threshold == 0.99


def test_auto_link_threshold_rejects_infinity():
    """Infinity is not a valid threshold."""
    with pytest.raises(ValidationError):
        _settings(auto_link_threshold=float("inf"))


def test_auto_link_threshold_rejects_nan():
    """NaN must not slip through — ge/le comparisons with NaN are False
    in Python, so Pydantic should reject it."""
    with pytest.raises(ValidationError):
        _settings(auto_link_threshold=float("nan"))
