from __future__ import annotations

from pathlib import Path
from typing import Iterable

import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer


class TfidfEmbedder:
    def __init__(self, model_path: str | Path) -> None:
        self.model_path = Path(model_path)
        self.vectorizer: TfidfVectorizer | None = None
        self.doc_matrix = None

    def fit(self, texts: Iterable[str]) -> None:
        corpus = list(texts)
        new_vectorizer = TfidfVectorizer(
            lowercase=True,
            ngram_range=(1, 2),
            max_features=32768,
            min_df=1,
            token_pattern=r"(?u)\b[A-Za-z0-9_./:-]{2,}\b",
        )
        if corpus:
            new_matrix = new_vectorizer.fit_transform(corpus)
        else:
            new_matrix = None
        # Atomically swap: concurrent transform() callers either see the old
        # fitted vectorizer or the new one, never a half-built state.
        self.vectorizer = new_vectorizer
        self.doc_matrix = new_matrix

    def transform(self, texts: Iterable[str]):
        if self.vectorizer is None:
            raise RuntimeError("Vectorizer not fitted")
        return self.vectorizer.transform(list(texts))

    def save(self) -> None:
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(
            {
                "vectorizer": self.vectorizer,
                "doc_matrix": self.doc_matrix,
            },
            self.model_path,
        )

    def load(self) -> bool:
        if not self.model_path.exists():
            return False
        payload = joblib.load(self.model_path)
        self.vectorizer = payload["vectorizer"]
        self.doc_matrix = payload["doc_matrix"]
        return True


def cosine_dense(matrix, vector) -> np.ndarray:
    if matrix is None:
        return np.array([])
    scores = matrix @ vector.T
    if hasattr(scores, "toarray"):
        scores = scores.toarray()
    scores = np.asarray(scores).reshape(-1)
    return scores
