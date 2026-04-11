"""Compute pairwise similarity between brain notes and produce wiki-link candidates."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Protocol

import numpy as np

from .hybrid_embeddings import HybridEmbedder

logger = logging.getLogger(__name__)


class _NoteLike(Protocol):
    owner_id: str
    path: str
    content: str


@dataclass(frozen=True)
class WikiLinkCandidate:
    """A pair of notes whose similarity exceeds the configured threshold.

    Candidates are deduplicated — for any pair (A, B), only (A, B) is returned,
    never also (B, A). The writer stage converts each candidate into
    bidirectional `related_notes` frontmatter entries.
    """

    source_owner_id: str
    target_owner_id: str
    source_path: str
    target_path: str
    similarity: float


def compute_wiki_link_candidates(
    notes: list[_NoteLike],
    embedder: HybridEmbedder,
    threshold: float,
) -> list[WikiLinkCandidate]:
    """Find all note pairs whose semantic similarity exceeds `threshold`.

    Uses the existing TF-IDF matrix on the embedder (pairwise cosine).
    Returns upper-triangle pairs only (i < j) — no self-pairs, no duplicates.
    """
    if len(notes) < 2:
        return []
    tfidf = embedder.tfidf
    if tfidf.doc_matrix is None or tfidf.vectorizer is None:
        logger.debug("TF-IDF matrix not fitted — skipping wiki-link computation")
        return []
    if tfidf.doc_matrix.shape[0] != len(notes):
        logger.warning(
            "TF-IDF matrix shape (%d) does not match notes count (%d) — "
            "likely a stale embedder. Skipping wiki-link computation.",
            tfidf.doc_matrix.shape[0], len(notes),
        )
        return []

    sim_matrix = (tfidf.doc_matrix @ tfidf.doc_matrix.T)
    if hasattr(sim_matrix, "toarray"):
        sim_matrix = sim_matrix.toarray()
    sim_matrix = np.asarray(sim_matrix)

    candidates: list[WikiLinkCandidate] = []
    n = len(notes)
    for i in range(n):
        for j in range(i + 1, n):
            score = float(sim_matrix[i, j])
            if score >= threshold:
                candidates.append(
                    WikiLinkCandidate(
                        source_owner_id=notes[i].owner_id,
                        target_owner_id=notes[j].owner_id,
                        source_path=notes[i].path,
                        target_path=notes[j].path,
                        similarity=score,
                    )
                )
    candidates.sort(key=lambda c: -c.similarity)
    return candidates
