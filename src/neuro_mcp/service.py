from __future__ import annotations

import logging
import os
import stat
import threading
from datetime import datetime, timezone
from pathlib import Path

# UTC compatibility for Python 3.10
try:
    from datetime import UTC
except ImportError:
    UTC = timezone.utc

from .codebase import scan_code_documents
from .config import Settings
from .embeddings import TfidfEmbedder
from .gc import build_gc_report
from .git_utils import detect_mode
from .hybrid_embeddings import HybridEmbedder
from .models import DigestReport, DocKind, Mode, ReconcileReport, SearchResult
from .notes import scan_brain_documents
from .reconcile import reconcile_results
from .search import dedupe_note_results, rank_documents, rank_documents_hybrid
from .storage import Repository

logger = logging.getLogger(__name__)


class NeuroMCPService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.data_dir = settings.data_dir
        self.repo = Repository(self.data_dir / "documents.sqlite3")
        self.brain_embedder = TfidfEmbedder(self.data_dir / "brain_index.joblib")
        self.code_embedder = TfidfEmbedder(self.data_dir / "code_index.joblib")
        cache_dir = Path(settings.semantic_cache_dir) if settings.semantic_cache_dir else self.data_dir / "models"
        self.brain_hybrid = HybridEmbedder(
            tfidf_embedder=self.brain_embedder,
            model_name=settings.semantic_model,
            cache_dir=cache_dir,
            semantic_weight=settings.semantic_model_weight,
            tfidf_weight=settings.tfidf_model_weight,
        )
        self.code_hybrid = HybridEmbedder(
            tfidf_embedder=self.code_embedder,
            model_name=settings.semantic_model,
            cache_dir=cache_dir,
            semantic_weight=settings.semantic_model_weight,
            tfidf_weight=settings.tfidf_model_weight,
        )
        self.notes = {}
        self.manifests: dict[str, set[str]] = {}
        self._loaded = False
        self._refresh_lock = threading.Lock()
        self._check_data_dir_permissions()

    def _check_data_dir_permissions(self) -> None:
        """Warn if data_dir is world-writable — joblib uses pickle, unsafe if writable by others."""
        data_dir = self.settings.data_dir
        if not data_dir.exists():
            return
        if os.name == "nt":
            return  # Windows permissions model is different
        try:
            mode = data_dir.stat().st_mode
            if mode & stat.S_IWOTH:
                logger.warning(
                    "data_dir '%s' is world-writable. "
                    "joblib index files use pickle — a malicious actor with write access "
                    "could execute arbitrary code on load. "
                    "Fix with: chmod o-w '%s'",
                    data_dir,
                    data_dir,
                )
        except OSError:
            pass

    def refresh(self) -> None:
        with self._refresh_lock:
            brain_docs, notes = scan_brain_documents(self.settings)
            code_docs, manifests = scan_code_documents(self.settings)

            self.repo.replace_kind(DocKind.BRAIN, brain_docs)
            self.repo.replace_kind(DocKind.CODE, code_docs)

            self.brain_hybrid.fit([doc.content for doc in brain_docs])
            self.code_hybrid.fit([doc.content for doc in code_docs])
            self.brain_embedder.save()
            self.code_embedder.save()

            self.notes = notes
            self.manifests = manifests
            self._loaded = True

    def load(self) -> None:
        """Load from persisted index if available, otherwise full refresh."""
        db_path = self.data_dir / "documents.sqlite3"
        brain_ok = self.brain_embedder.load()
        code_ok = self.code_embedder.load()
        if brain_ok and code_ok and db_path.exists():
            # Restore notes metadata from brain documents
            brain_docs = self.repo.all_documents(DocKind.BRAIN)
            if brain_docs:
                from .notes import _rebuild_notes_from_docs
                self.notes = _rebuild_notes_from_docs(brain_docs)
                self._loaded = True
                logger.info("Loaded from persisted index (%d brain, %d code docs)",
                            len(brain_docs), len(self.repo.all_documents(DocKind.CODE)))
                return
        # Fallback: full refresh from filesystem
        self.refresh()

    def _ensure_loaded(self) -> None:
        if not self._loaded:
            self.load()

    def current_mode(self) -> Mode:
        change_set = detect_mode(self.settings.code_root, threshold=self.settings.phasic_change_threshold)
        return change_set.mode

    def search_brain(self, query: str, top_k: int | None = None) -> list[SearchResult]:
        self._ensure_loaded()
        docs = self.repo.all_documents(DocKind.BRAIN)
        ranked = rank_documents_hybrid(
            query,
            docs,
            self.brain_hybrid,
            top_k=max((top_k or self.settings.search_top_k) * 4, 10),
            semantic_weight=self.settings.semantic_weight,
            lexical_weight=self.settings.lexical_weight,
            freshness_weight=self.settings.freshness_weight,
            precision_weight=self.settings.precision_weight,
        )
        deduped = dedupe_note_results(ranked, top_k or self.settings.search_top_k)
        for item in deduped:
            item.source_of_truth = "brain"
        return deduped

    def search_codebase(self, query: str, top_k: int | None = None) -> list[SearchResult]:
        self._ensure_loaded()
        docs = self.repo.all_documents(DocKind.CODE)
        ranked = rank_documents_hybrid(
            query,
            docs,
            self.code_hybrid,
            top_k=top_k or self.settings.search_top_k,
            semantic_weight=self.settings.semantic_weight,
            lexical_weight=self.settings.lexical_weight,
            freshness_weight=0.0,
            precision_weight=0.15,
        )
        for item in ranked:
            item.source_of_truth = "code"
            item.freshness = "current"
            item.status = "active"
            item.source_precision = 1.0
            item.last_verified = datetime.now(UTC).isoformat().replace("+00:00", "Z")
        return ranked

    def reconcile(self, query: str, top_k: int | None = None) -> ReconcileReport:
        brain_results = self.search_brain(query, top_k=top_k)
        code_results = self.search_codebase(query, top_k=top_k)
        report = reconcile_results(
            query=query,
            brain_results=brain_results,
            code_results=code_results,
            manifests=self.manifests,
            mode=self.current_mode(),
        )
        truth = report.source_of_truth
        if truth == "code":
            for item in report.brain_results:
                item.source_of_truth = "code"
        else:
            for item in report.brain_results:
                item.source_of_truth = "brain+code"
        return report

    def gc(self, dry_run: bool = True):
        self._ensure_loaded()
        notes = [note.model_dump() for note in self.notes.values()]
        report = build_gc_report(notes, self.current_mode(), dry_run=dry_run)
        if not dry_run and report.items:
            from .gc import execute_gc_actions
            backup_dir = self.data_dir / "gc_backups"
            execute_gc_actions(report.items, backup_dir=backup_dir)
        return report

    def digest(self) -> DigestReport:
        self._ensure_loaded()
        total = len(self.notes)
        stale = 0
        labile = 0
        missing_sources = 0
        risks: list[str] = []

        for note in self.notes.values():
            if note.freshness.value in {"stale", "missing_sources"}:
                stale += 1
            if note.status.value == "labile":
                labile += 1
            if not note.source_files_exist:
                missing_sources += 1
                risks.append(f"Missing source path in {note.title}")

        next_actions = []
        if stale:
            next_actions.append("Run freshness verification on stale notes.")
        if missing_sources:
            next_actions.append("Run garbage collection and relink missing source paths.")
        if self.current_mode() == Mode.TONIC:
            next_actions.append("Major code volatility detected: run full reconcile audit.")

        return DigestReport(
            generated_at=datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            mode=self.current_mode(),
            total_notes=total,
            stale_notes=stale,
            labile_notes=labile,
            missing_source_notes=missing_sources,
            top_risks=risks[:10],
            next_actions=next_actions,
        )

    def get_note(self, relative_path: str) -> dict:
        """Retrieve a specific brain note by relative path."""
        full_path = (self.settings.brain_root / relative_path).resolve()
        if not full_path.is_relative_to(self.settings.brain_root.resolve()):
            return {"found": False, "path": relative_path, "error": "Path traversal outside brain root"}
        if not full_path.exists() or not full_path.is_file():
            return {"found": False, "path": relative_path, "error": "Note not found"}

        from .frontmatter import parse_markdown_note
        from .freshness import compute_freshness
        from .notes import _coerce_list, _guess_note_type, _parse_datetime

        metadata_raw, body = parse_markdown_note(full_path)
        rel = Path(relative_path)
        note_type = _guess_note_type(rel, metadata_raw)
        decay_class = metadata_raw.get("decay_class") or None
        last_verified = _parse_datetime(metadata_raw.get("last_verified"))
        linked_paths = _coerce_list(metadata_raw.get("linked_paths") or metadata_raw.get("source_files"))
        source_files_exist = all(
            (self.settings.code_root / lp).exists() for lp in linked_paths
        ) if linked_paths else True

        freshness = compute_freshness(
            note_type=note_type,
            decay_class=decay_class,
            last_verified=last_verified,
            source_files_exist=source_files_exist,
            immutable_note_types=self.settings.immutable_note_types,
        )

        return {
            "found": True,
            "path": relative_path,
            "title": str(metadata_raw.get("title") or rel.stem),
            "content": body.strip(),
            "metadata": {
                "note_type": note_type,
                "status": str(metadata_raw.get("status") or freshness.recommended_status.value),
                "decay_class": decay_class,
                "source_precision": float(metadata_raw.get("source_precision", 0.5)),
                "freshness": freshness.freshness.value,
                "stale_reasons": freshness.stale_reasons,
                "tags": _coerce_list(metadata_raw.get("tags")),
                "last_verified": str(last_verified) if last_verified else None,
                "linked_paths": linked_paths,
                "source_files_exist": source_files_exist,
            },
        }

    def get_related(self, relative_path: str, top_k: int = 5) -> dict:
        """Find notes semantically related to a given note."""
        full_path = self.settings.brain_root / relative_path
        if not full_path.exists():
            return {"found": False, "path": relative_path, "error": "Note not found"}

        self._ensure_loaded()
        from .frontmatter import parse_markdown_note
        _, body = parse_markdown_note(full_path)

        results = self.search_brain(body.strip()[:500], top_k=top_k + 5)
        filtered = [r for r in results if not r.path.endswith(relative_path)][:top_k]

        return {
            "found": True,
            "path": relative_path,
            "related": [
                {
                    "title": r.title,
                    "path": str(Path(r.path).relative_to(self.settings.brain_root)) if str(r.path).startswith(str(self.settings.brain_root)) else r.path,
                    "relevance": r.relevance,
                    "freshness": r.freshness,
                    "snippet": r.snippet,
                }
                for r in filtered
            ],
        }

    def ingest_note(
        self,
        relative_path: str,
        title: str,
        content: str,
        note_type: str = "note",
        tags: list[str] | None = None,
        decay_class: str = "30d",
        source_precision: float = 0.7,
        claimed_dependencies: list[str] | None = None,
    ) -> dict:
        """Write a new note or update existing. Returns creation status."""
        from .writer import write_note
        result = write_note(
            brain_root=self.settings.brain_root,
            relative_path=relative_path,
            title=title,
            content=content,
            note_type=note_type,
            tags=tags,
            decay_class=decay_class,
            source_precision=source_precision,
            claimed_dependencies=claimed_dependencies,
        )
        self._loaded = False
        return result

    def status(self) -> dict:
        """Return overall brain health overview."""
        self._ensure_loaded()
        by_type: dict[str, int] = {}
        by_status: dict[str, int] = {}
        by_freshness: dict[str, int] = {}

        for note in self.notes.values():
            by_type[note.note_type] = by_type.get(note.note_type, 0) + 1
            by_status[note.status.value] = by_status.get(note.status.value, 0) + 1
            by_freshness[note.freshness.value] = by_freshness.get(note.freshness.value, 0) + 1

        stale = by_freshness.get("stale", 0) + by_freshness.get("missing_sources", 0)
        recs = []
        if stale > 0:
            recs.append(f"{stale} notes need freshness verification.")
        if by_status.get("labile", 0) > 0:
            recs.append(f"{by_status['labile']} labile notes need review.")
        mode = self.current_mode()
        if mode == Mode.TONIC:
            recs.append("Tonic mode: major code changes detected — run full reconcile.")

        return {
            "total_notes": len(self.notes),
            "by_type": by_type,
            "by_status": by_status,
            "by_freshness": by_freshness,
            "mode": mode.value,
            "has_semantic": self.brain_hybrid.has_semantic,
            "recommendations": recs,
        }

    def check_interference(self) -> dict:
        """Check brain notes for high-similarity overlaps."""
        self._ensure_loaded()
        docs = self.repo.all_documents(DocKind.BRAIN)
        if not docs:
            return {"candidates": [], "threshold": self.settings.similarity_threshold, "total_docs": 0}

        import numpy as np
        # Get embeddings — prefer semantic, fall back to TF-IDF
        if self.brain_hybrid.has_semantic and self.brain_hybrid._doc_embeddings is not None:
            embeddings = self.brain_hybrid._doc_embeddings
        elif self.brain_embedder.doc_matrix is not None:
            embeddings = self.brain_embedder.doc_matrix.toarray()
        else:
            return {"candidates": [], "threshold": self.settings.similarity_threshold, "total_docs": len(docs)}

        from .interference import check_interference as _check

        paths = [d.path for d in docs]
        owner_ids = [d.owner_id for d in docs]
        emb_array = np.asarray(embeddings)

        candidates = _check(emb_array, paths, owner_ids, threshold=self.settings.similarity_threshold)

        return {
            "candidates": [
                {
                    "note_a": c.note_a_path,
                    "note_b": c.note_b_path,
                    "similarity": round(c.similarity, 4),
                    "action": c.action,
                    "reason": c.reason,
                }
                for c in candidates
            ],
            "threshold": self.settings.similarity_threshold,
            "total_docs": len(docs),
        }
