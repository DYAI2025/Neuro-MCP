from __future__ import annotations

from datetime import datetime
from typing import Iterable

from .embeddings import TfidfEmbedder, cosine_dense
from .freshness import freshness_bonus
from .models import DocKind, DocumentRecord, SearchResult
from .text_utils import keyword_score


def rank_documents(
    query: str,
    documents: list[DocumentRecord],
    embedder: TfidfEmbedder,
    *,
    top_k: int,
    semantic_weight: float,
    lexical_weight: float,
    freshness_weight: float,
    precision_weight: float,
) -> list[SearchResult]:
    if not documents:
        return []
    if embedder.vectorizer is None or embedder.doc_matrix is None:
        return []

    query_vector = embedder.transform([query])
    semantic_scores = cosine_dense(embedder.doc_matrix, query_vector)
    results: list[SearchResult] = []
    for document, semantic in zip(documents, semantic_scores, strict=False):
        metadata = document.metadata
        freshness = metadata.get("freshness", "current")
        source_precision = float(metadata.get("source_precision", 0.5))
        lexical = keyword_score(query, document.content, document.path)
        freshness_value = freshness_bonus(_coerce_freshness(freshness))
        relevance = (
            semantic_weight * float(semantic)
            + lexical_weight * float(lexical)
            + freshness_weight * float(freshness_value)
            + precision_weight * source_precision
        )
        last_verified = metadata.get("last_verified")
        if isinstance(last_verified, str) and last_verified.endswith("+00:00"):
            last_verified = last_verified.replace("+00:00", "Z")
        results.append(
            SearchResult(
                kind=document.kind,
                owner_id=document.owner_id,
                path=document.path,
                title=document.title,
                snippet=document.snippet,
                uri=document.uri,
                relevance=round(relevance, 6),
                lexical_score=round(float(lexical), 6),
                semantic_score=round(float(semantic), 6),
                freshness=str(freshness),
                status=str(metadata.get("status", "active")),
                source_precision=source_precision,
                last_verified=last_verified,
                source_files_exist=bool(metadata.get("source_files_exist", True)),
                stale_reasons=list(metadata.get("stale_reasons", [])),
                note_type=metadata.get("note_type"),
                line_start=document.line_start,
                line_end=document.line_end,
                metadata=metadata,
            )
        )
    results.sort(key=lambda item: item.relevance, reverse=True)
    return results[:top_k]


def dedupe_note_results(results: Iterable[SearchResult], limit: int) -> list[SearchResult]:
    deduped: list[SearchResult] = []
    seen: set[str] = set()
    for result in results:
        if result.owner_id in seen and result.kind == DocKind.BRAIN:
            continue
        seen.add(result.owner_id)
        deduped.append(result)
        if len(deduped) >= limit:
            break
    return deduped


def _coerce_freshness(value: str):
    from .models import FreshnessState

    try:
        return FreshnessState(value)
    except ValueError:
        return FreshnessState.CURRENT


def rank_documents_hybrid(
    query: str,
    documents: list[DocumentRecord],
    hybrid_embedder,  # HybridEmbedder — no type import to avoid circular
    *,
    top_k: int = 5,
    semantic_weight: float = 0.55,
    lexical_weight: float = 0.20,
    freshness_weight: float = 0.15,
    precision_weight: float = 0.10,
) -> list[SearchResult]:
    """Rank documents using the HybridEmbedder (TF-IDF + optional sentence-transformers)."""
    if not documents:
        return []

    tfidf_scores, semantic_scores = hybrid_embedder.score(query)
    if len(tfidf_scores) == 0 and len(semantic_scores) == 0:
        return []

    results: list[SearchResult] = []
    for idx, document in enumerate(documents):
        metadata = document.metadata
        freshness = metadata.get("freshness", "current")
        source_precision = float(metadata.get("source_precision", 0.5))
        lexical = keyword_score(query, document.content, document.path)
        freshness_value = freshness_bonus(_coerce_freshness(freshness))

        tfidf_s = float(tfidf_scores[idx]) if idx < len(tfidf_scores) else 0.0
        semantic_s = float(semantic_scores[idx]) if idx < len(semantic_scores) else 0.0
        combined_semantic = (
            hybrid_embedder.tfidf_weight * tfidf_s
            + hybrid_embedder.semantic_weight * semantic_s
        )

        relevance = (
            semantic_weight * combined_semantic
            + lexical_weight * float(lexical)
            + freshness_weight * float(freshness_value)
            + precision_weight * source_precision
        )

        last_verified = metadata.get("last_verified")
        if isinstance(last_verified, str) and last_verified.endswith("+00:00"):
            last_verified = last_verified.replace("+00:00", "Z")

        results.append(
            SearchResult(
                kind=document.kind,
                owner_id=document.owner_id,
                path=document.path,
                title=document.title,
                snippet=document.snippet,
                uri=document.uri,
                relevance=round(relevance, 6),
                lexical_score=round(float(lexical), 6),
                semantic_score=round(combined_semantic, 6),
                freshness=str(freshness),
                status=str(metadata.get("status", "active")),
                source_precision=source_precision,
                last_verified=last_verified,
                source_files_exist=bool(metadata.get("source_files_exist", True)),
                stale_reasons=list(metadata.get("stale_reasons", [])),
                note_type=metadata.get("note_type"),
                line_start=document.line_start,
                line_end=document.line_end,
                metadata=metadata,
            )
        )
    results.sort(key=lambda item: item.relevance, reverse=True)
    return results[:top_k]
