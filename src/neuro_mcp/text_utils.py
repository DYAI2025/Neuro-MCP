from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Iterable


WORD_RE = re.compile(r"[A-Za-z0-9_\-./]+")


def stable_id(*parts: str) -> str:
    digest = hashlib.sha1("||".join(parts).encode("utf-8")).hexdigest()
    return digest


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def make_snippet(text: str, limit: int = 280) -> str:
    clean = normalize_text(text)
    if len(clean) <= limit:
        return clean
    return clean[: limit - 3].rstrip() + "..."


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in WORD_RE.findall(text)]


def keyword_score(query: str, text: str, path: str = "") -> float:
    tokens = tokenize(query)
    haystack = " ".join([text.lower(), path.lower()])
    if not tokens:
        return 0.0
    hits = sum(1 for token in tokens if token in haystack)
    exact = 1.0 if normalize_text(query).lower() in haystack else 0.0
    return min(1.0, (hits / len(tokens)) * 0.8 + exact * 0.2)


def path_is_excluded(path: Path, exclude_dirs: Iterable[str]) -> bool:
    parts = set(path.parts)
    return any(part in parts for part in exclude_dirs)
