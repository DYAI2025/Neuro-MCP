from __future__ import annotations

from neuro_mcp.embeddings import TfidfEmbedder
from neuro_mcp.hybrid_embeddings import HybridEmbedder
from neuro_mcp.models import DocKind, DocumentRecord
from neuro_mcp.search import rank_documents_hybrid


def _make_doc(doc_id: str, content: str, title: str = "test", freshness: str = "current", precision: float = 0.8) -> DocumentRecord:
    return DocumentRecord(
        doc_id=doc_id,
        kind=DocKind.BRAIN,
        owner_id=f"owner-{doc_id}",
        path=f"/tmp/{doc_id}.md",
        uri=f"brain://{doc_id}",
        title=title,
        content=content,
        snippet=content[:80],
        line_start=1,
        line_end=10,
        content_hash=doc_id,
        metadata={"freshness": freshness, "source_precision": precision, "status": "active"},
    )


def test_rank_documents_hybrid_returns_sorted():
    docs = [
        _make_doc("a", "CentralBridge is the main bridge module for profile data"),
        _make_doc("b", "Database migration scripts for PostgreSQL"),
        _make_doc("c", "Frontend component for displaying charts"),
    ]
    tfidf = TfidfEmbedder(model_path="/tmp/test_search_tfidf.joblib")
    hybrid = HybridEmbedder(tfidf_embedder=tfidf, model_name=None)
    hybrid.fit([d.content for d in docs])

    results = rank_documents_hybrid(
        query="CentralBridge module",
        documents=docs,
        hybrid_embedder=hybrid,
        top_k=3,
        semantic_weight=0.55,
        lexical_weight=0.20,
        freshness_weight=0.15,
        precision_weight=0.10,
    )
    assert len(results) == 3
    assert results[0].relevance >= results[1].relevance


def test_rank_documents_hybrid_empty():
    tfidf = TfidfEmbedder(model_path="/tmp/test_search_empty.joblib")
    hybrid = HybridEmbedder(tfidf_embedder=tfidf, model_name=None)
    hybrid.fit([])
    results = rank_documents_hybrid("anything", [], hybrid, top_k=5)
    assert results == []
