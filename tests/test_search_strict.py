"""Test that search raises on length mismatch between documents and scores."""
from __future__ import annotations

import numpy as np
import pytest

from neuro_mcp.models import DocKind, DocumentRecord
from neuro_mcp.embeddings import TfidfEmbedder
from neuro_mcp.search import rank_documents


def _make_docs(n: int) -> list[DocumentRecord]:
    return [
        DocumentRecord(
            doc_id=f"d{i}",
            kind=DocKind.BRAIN,
            owner_id=f"o{i}",
            path=f"note{i}.md",
            uri=f"file:///note{i}.md",
            title=f"Note {i}",
            content=f"content about topic {i}",
            snippet=f"snippet {i}",
            line_start=0,
            line_end=10,
            content_hash=f"hash{i}",
            metadata={"freshness": "current", "source_precision": 0.5},
        )
        for i in range(n)
    ]


def test_rank_documents_length_mismatch_raises(tmp_path):
    """If embedder produces fewer scores than documents, should raise ValueError."""
    docs = _make_docs(5)
    embedder = TfidfEmbedder(tmp_path / "model.joblib")
    embedder.fit(["topic one", "topic two", "topic three"])
    with pytest.raises(ValueError, match="[Mm]ismatch"):
        rank_documents(
            "topic",
            docs,
            embedder,
            top_k=5,
            semantic_weight=0.55,
            lexical_weight=0.20,
            freshness_weight=0.15,
            precision_weight=0.10,
        )


def test_rank_documents_matching_length_works(tmp_path):
    """Normal case: same number of docs and scores."""
    docs = _make_docs(3)
    embedder = TfidfEmbedder(tmp_path / "model.joblib")
    embedder.fit([d.content for d in docs])
    results = rank_documents(
        "topic",
        docs,
        embedder,
        top_k=3,
        semantic_weight=0.55,
        lexical_weight=0.20,
        freshness_weight=0.15,
        precision_weight=0.10,
    )
    assert len(results) == 3
