"""Hybrid embedder combining TF-IDF (lexical precision) with sentence-transformers (semantic understanding)."""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

from .embeddings import TfidfEmbedder, cosine_dense

if TYPE_CHECKING:
    pass


class HybridEmbedder:
    """Wraps TfidfEmbedder and optionally adds sentence-transformer scoring.

    If ``model_name`` is None or sentence-transformers is not installed, falls
    back to TF-IDF only — no crash, no import error.
    """

    def __init__(
        self,
        tfidf_embedder: TfidfEmbedder,
        model_name: str | None = "all-MiniLM-L6-v2",
        cache_dir: Path | None = None,
        semantic_weight: float = 0.65,
        tfidf_weight: float = 0.35,
    ) -> None:
        self.tfidf = tfidf_embedder
        self.model_name = model_name
        self.cache_dir = cache_dir
        self.semantic_weight = semantic_weight
        self.tfidf_weight = tfidf_weight
        self._model = None
        self._doc_embeddings: np.ndarray | None = None
        self._has_st: bool | None = None

    @property
    def has_semantic(self) -> bool:
        if self._has_st is None:
            if self.model_name is None:
                self._has_st = False
            else:
                try:
                    import sentence_transformers  # noqa: F401
                    self._has_st = True
                except ImportError:
                    self._has_st = False
        return self._has_st

    def _load_model(self) -> bool:
        if self._model is not None:
            return True
        if not self.has_semantic:
            return False
        from sentence_transformers import SentenceTransformer
        kwargs = {}
        if self.cache_dir:
            kwargs["cache_folder"] = str(self.cache_dir)
        self._model = SentenceTransformer(self.model_name, **kwargs)
        return True

    def fit(self, texts: list[str]) -> None:
        self.tfidf.fit(texts)
        if self._load_model() and texts:
            self._doc_embeddings = self._model.encode(
                texts, normalize_embeddings=True, show_progress_bar=False,
            )
        else:
            self._doc_embeddings = None

    def score(self, query: str) -> tuple[np.ndarray, np.ndarray]:
        tfidf_scores = np.zeros(0)
        if self.tfidf.vectorizer is not None and self.tfidf.doc_matrix is not None:
            query_vec = self.tfidf.transform([query])
            tfidf_scores = cosine_dense(self.tfidf.doc_matrix, query_vec)

        n = len(tfidf_scores) if len(tfidf_scores) > 0 else 0
        if self._model is not None and self._doc_embeddings is not None:
            q_emb = self._model.encode([query], normalize_embeddings=True)
            semantic_scores = (self._doc_embeddings @ q_emb.T).reshape(-1)
        else:
            semantic_scores = np.zeros(n)

        return tfidf_scores, semantic_scores

    def combined_scores(self, query: str) -> np.ndarray:
        tfidf_scores, semantic_scores = self.score(query)
        if len(tfidf_scores) == 0:
            return semantic_scores
        if len(semantic_scores) == 0:
            return tfidf_scores
        return self.tfidf_weight * tfidf_scores + self.semantic_weight * semantic_scores

    def encode_single(self, text: str) -> np.ndarray | None:
        if self._model is None:
            return None
        return self._model.encode([text], normalize_embeddings=True)[0]
