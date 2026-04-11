"""Compute pairwise similarity between brain notes and produce wiki-link candidates."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import numpy as np

from .frontmatter import (
    dump_markdown_note,
    parse_markdown_note,
    stamp_enrichment_marker,
)
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


def _note_link(path: Path) -> str:
    """Convert a note path into an Obsidian wiki-link (by stem)."""
    return f"[[{path.stem}]]"


def _append_link(meta: dict, link: str) -> bool:
    """Add `link` to `meta["related_notes"]` if not already present.

    Returns True if the list was modified.
    """
    existing = meta.get("related_notes") or []
    if not isinstance(existing, list):
        existing = [existing]
    if link in existing:
        return False
    existing.append(link)
    meta["related_notes"] = existing
    return True


def write_wiki_links(
    candidates: list[WikiLinkCandidate],
    brain_root: Path,
) -> list[str]:
    """Write bidirectional wiki-links into frontmatter for each candidate pair.

    For each `WikiLinkCandidate(a, b)`:
      - `a.md` gets `[[b_stem]]` appended to `related_notes`
      - `b.md` gets `[[a_stem]]` appended to `related_notes`

    Existing `related_notes` entries are preserved. Duplicate links are not
    re-added (idempotent). The enrichment marker is stamped on every modified
    note.

    Body content is never modified (DEC-two-stage-mutations).

    Returns the list of paths that were actually modified.
    """
    modified_paths: set[str] = set()
    file_changes: dict[Path, dict] = {}

    def _get_meta(path: Path) -> dict | None:
        if path in file_changes:
            return file_changes[path]
        if not path.exists():
            logger.debug("Wiki-link writer: file missing, skipping %s", path)
            return None
        meta, body = parse_markdown_note(path)
        file_changes[path] = {"meta": meta, "body": body, "changed": False}
        return file_changes[path]

    brain_root_resolved = brain_root.resolve()
    for cand in candidates:
        source = Path(cand.source_path)
        target = Path(cand.target_path)
        try:
            if not source.resolve().is_relative_to(brain_root_resolved) or \
               not target.resolve().is_relative_to(brain_root_resolved):
                logger.warning(
                    "Wiki-link: path outside brain_root, skipping %s <-> %s",
                    source, target,
                )
                continue
        except (OSError, ValueError):
            logger.warning("Wiki-link: path resolution failed, skipping %s <-> %s", source, target)
            continue
        src_entry = _get_meta(source)
        tgt_entry = _get_meta(target)
        if src_entry is None or tgt_entry is None:
            continue

        target_link = _note_link(target)
        source_link = _note_link(source)

        if _append_link(src_entry["meta"], target_link):
            src_entry["changed"] = True
        if _append_link(tgt_entry["meta"], source_link):
            tgt_entry["changed"] = True

    for path, entry in file_changes.items():
        if not entry["changed"]:
            continue
        stamp_enrichment_marker(entry["meta"])
        path.write_text(
            dump_markdown_note(entry["meta"], entry["body"]),
            encoding="utf-8",
        )
        modified_paths.add(str(path))
        logger.info("Wiki-link: wrote related_notes to %s", path)

    return sorted(modified_paths)
