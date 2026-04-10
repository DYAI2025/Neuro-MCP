"""Interference detection: find overlapping/contradicting notes via embedding similarity."""
from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class InterferenceCandidate:
    note_a_path: str
    note_b_path: str
    similarity: float
    action: str   # "merge" | "cross_link" | "supersede"
    reason: str


def check_interference(
    embeddings: np.ndarray,
    paths: list[str],
    owner_ids: list[str],
    threshold: float = 0.85,
    max_documents: int = 1000,
) -> list[InterferenceCandidate]:
    """Pairwise cosine similarity check. Returns candidates above threshold.

    - Same owner_id -> merge candidate (sections of same note are near-duplicates)
    - Different owner_id -> cross_link candidate (different notes overlap)

    If more than *max_documents* are provided, the input is truncated and a
    warning is logged. This prevents O(n^2) blowup on large note bases.
    """
    n = len(paths)
    if n < 2 or embeddings.shape[0] < 2:
        return []

    if n > max_documents:
        logger.warning(
            "Interference check capped: %d documents truncated to %d (O(n^2) safety limit)",
            n,
            max_documents,
        )
        embeddings = embeddings[:max_documents]
        paths = paths[:max_documents]
        owner_ids = owner_ids[:max_documents]
        n = max_documents

    # Normalize if not already
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1.0, norms)
    normed = embeddings / norms

    sim_matrix = normed @ normed.T

    candidates: list[InterferenceCandidate] = []
    for i in range(n):
        for j in range(i + 1, n):
            score = float(sim_matrix[i, j])
            if score >= threshold:
                if owner_ids[i] == owner_ids[j]:
                    action = "merge"
                    reason = f"Same note sections overlap (cosine={score:.3f})"
                else:
                    action = "cross_link"
                    reason = f"Different notes overlap (cosine={score:.3f})"
                candidates.append(InterferenceCandidate(
                    note_a_path=paths[i],
                    note_b_path=paths[j],
                    similarity=score,
                    action=action,
                    reason=reason,
                ))
    candidates.sort(key=lambda c: c.similarity, reverse=True)
    return candidates
