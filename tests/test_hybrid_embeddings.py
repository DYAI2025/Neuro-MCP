from __future__ import annotations

import numpy as np
import pytest


def test_hybrid_embedder_fit_and_score_tfidf_only():
    from neuro_mcp.embeddings import TfidfEmbedder
    from neuro_mcp.hybrid_embeddings import HybridEmbedder

    tfidf = TfidfEmbedder(model_path="/tmp/test_tfidf.joblib")
    hybrid = HybridEmbedder(tfidf_embedder=tfidf, model_name=None)

    texts = [
        "RingStory is the central bridge object",
        "Authentication uses Supabase Auth with JWT tokens",
        "The frontend is built with Next.js and shadcn/ui",
    ]
    hybrid.fit(texts)

    tfidf_scores, semantic_scores = hybrid.score("RingStory bridge")
    assert len(tfidf_scores) == 3
    assert len(semantic_scores) == 3
    assert np.allclose(semantic_scores, 0.0)
    assert tfidf_scores[0] > tfidf_scores[1]


def test_hybrid_embedder_combined_scores():
    from neuro_mcp.embeddings import TfidfEmbedder
    from neuro_mcp.hybrid_embeddings import HybridEmbedder

    tfidf = TfidfEmbedder(model_path="/tmp/test_tfidf2.joblib")
    hybrid = HybridEmbedder(
        tfidf_embedder=tfidf,
        model_name=None,
        semantic_weight=0.6,
        tfidf_weight=0.4,
    )

    texts = ["hello world", "foo bar"]
    hybrid.fit(texts)

    combined = hybrid.combined_scores("hello")
    assert len(combined) == 2
    assert combined[0] > combined[1]


def test_hybrid_embedder_with_sentence_transformers():
    pytest.importorskip("sentence_transformers")
    from neuro_mcp.embeddings import TfidfEmbedder
    from neuro_mcp.hybrid_embeddings import HybridEmbedder

    tfidf = TfidfEmbedder(model_path="/tmp/test_tfidf3.joblib")
    hybrid = HybridEmbedder(
        tfidf_embedder=tfidf,
        model_name="all-MiniLM-L6-v2",
        semantic_weight=0.65,
        tfidf_weight=0.35,
    )

    texts = [
        "The personality profiling data structure",
        "Authentication flow with JWT",
        "Database schema for user records",
    ]
    hybrid.fit(texts)

    tfidf_scores, semantic_scores = hybrid.score("character analysis object")
    assert semantic_scores[0] > semantic_scores[1]
    combined = hybrid.combined_scores("character analysis object")
    assert combined[0] > combined[1]


def test_hybrid_embedder_empty_corpus():
    from neuro_mcp.embeddings import TfidfEmbedder
    from neuro_mcp.hybrid_embeddings import HybridEmbedder

    tfidf = TfidfEmbedder(model_path="/tmp/test_tfidf_empty.joblib")
    hybrid = HybridEmbedder(tfidf_embedder=tfidf, model_name=None)
    hybrid.fit([])
    combined = hybrid.combined_scores("anything")
    assert len(combined) == 0


def test_hybrid_has_semantic_false_when_none():
    from neuro_mcp.embeddings import TfidfEmbedder
    from neuro_mcp.hybrid_embeddings import HybridEmbedder

    tfidf = TfidfEmbedder(model_path="/tmp/test_tfidf_nosem.joblib")
    hybrid = HybridEmbedder(tfidf_embedder=tfidf, model_name=None)
    assert hybrid.has_semantic is False
