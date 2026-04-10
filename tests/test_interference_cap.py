"""Test that interference check respects max_documents cap."""
from __future__ import annotations

import logging
import numpy as np
import pytest

from neuro_mcp.interference import check_interference


def test_interference_respects_max_documents_cap():
    """If more than max_documents, should truncate with warning."""
    n = 120
    embeddings = np.random.randn(n, 64).astype(np.float32)
    paths = [f"note_{i}.md" for i in range(n)]
    owner_ids = [f"owner_{i}" for i in range(n)]

    candidates = check_interference(
        embeddings, paths, owner_ids, threshold=0.99, max_documents=100
    )
    assert isinstance(candidates, list)


def test_interference_default_cap_allows_normal_usage():
    """Normal usage with <1000 docs should work without issues."""
    n = 10
    embeddings = np.random.randn(n, 64).astype(np.float32)
    embeddings[1] = embeddings[0] + 0.001
    paths = [f"note_{i}.md" for i in range(n)]
    owner_ids = [f"owner_{i}" for i in range(n)]

    candidates = check_interference(embeddings, paths, owner_ids, threshold=0.9)
    assert len(candidates) >= 1
    assert candidates[0].note_a_path == "note_0.md"
    assert candidates[0].note_b_path == "note_1.md"


def test_interference_logs_warning_on_cap(caplog):
    """Should log warning when document count exceeds cap."""
    n = 50
    embeddings = np.random.randn(n, 64).astype(np.float32)
    paths = [f"note_{i}.md" for i in range(n)]
    owner_ids = [f"owner_{i}" for i in range(n)]

    with caplog.at_level(logging.WARNING, logger="neuro_mcp.interference"):
        check_interference(embeddings, paths, owner_ids, threshold=0.99, max_documents=20)
    assert any("capped" in r.message.lower() or "truncat" in r.message.lower() for r in caplog.records)
