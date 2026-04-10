"""Test config weight validation."""
from __future__ import annotations

import pytest
from pydantic import ValidationError
from neuro_mcp.config import Settings


def test_search_weights_must_sum_to_one():
    with pytest.raises(ValidationError, match="[Ww]eight"):
        Settings(
            brain_root="/tmp/b",
            code_root="/tmp/c",
            semantic_weight=0.9,
            lexical_weight=0.9,
            freshness_weight=0.9,
            precision_weight=0.9,
        )


def test_hybrid_weights_must_sum_to_one():
    with pytest.raises(ValidationError, match="[Ww]eight"):
        Settings(
            brain_root="/tmp/b",
            code_root="/tmp/c",
            semantic_model_weight=0.8,
            tfidf_model_weight=0.8,
        )


def test_default_weights_are_valid():
    s = Settings(brain_root="/tmp/b", code_root="/tmp/c")
    total = s.semantic_weight + s.lexical_weight + s.freshness_weight + s.precision_weight
    assert abs(total - 1.0) < 0.01
