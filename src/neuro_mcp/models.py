from __future__ import annotations

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class NoteStatus(str, Enum):
    ACTIVE = "active"
    STALE = "stale"
    LABILE = "labile"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"


class FreshnessState(str, Enum):
    IMMUTABLE = "immutable"
    CURRENT = "current"
    AGING = "aging"
    STALE = "stale"
    MISSING_SOURCES = "missing_sources"


class DocKind(str, Enum):
    BRAIN = "brain"
    CODE = "code"


class Mode(str, Enum):
    PHASIC = "phasic"
    TONIC = "tonic"


class NoteMetadata(BaseModel):
    note_id: str
    title: str
    path: str
    note_type: str = "note"
    status: NoteStatus = NoteStatus.ACTIVE
    created: datetime | None = None
    last_verified: datetime | None = None
    decay_class: str = "30d"
    source_precision: float = 0.5
    source_type: str = "manual"
    tags: list[str] = Field(default_factory=list)
    linked_paths: list[str] = Field(default_factory=list)
    claimed_dependencies: list[str] = Field(default_factory=list)
    linked_commits: list[str] = Field(default_factory=list)
    superseded_by: str | None = None
    source_files_exist: bool = True
    freshness: FreshnessState = FreshnessState.CURRENT
    stale_reasons: list[str] = Field(default_factory=list)
    extra: dict[str, Any] = Field(default_factory=dict)


class DocumentRecord(BaseModel):
    doc_id: str
    kind: DocKind
    owner_id: str
    path: str
    uri: str
    title: str
    content: str
    snippet: str
    line_start: int = 1
    line_end: int = 1
    content_hash: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class SearchResult(BaseModel):
    kind: DocKind
    owner_id: str
    path: str
    title: str
    snippet: str
    uri: str
    relevance: float
    lexical_score: float
    semantic_score: float
    freshness: str
    status: str
    source_precision: float
    last_verified: str | None
    source_files_exist: bool
    stale_reasons: list[str] = Field(default_factory=list)
    note_type: str | None = None
    line_start: int | None = None
    line_end: int | None = None
    source_of_truth: str | None = None
    contradictions: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ReconcileReport(BaseModel):
    query: str
    source_of_truth: str
    mode: Mode
    brain_results: list[SearchResult]
    code_results: list[SearchResult]
    contradictions: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)


class GarbageCollectionItem(BaseModel):
    note_id: str
    path: str
    action: str
    reason: str
    status_before: str
    status_after: str


class GarbageCollectionReport(BaseModel):
    dry_run: bool
    mode: Mode
    items: list[GarbageCollectionItem] = Field(default_factory=list)
    total_notes: int = 0
    stale_count: int = 0
    missing_sources_count: int = 0
    archived_candidates: int = 0
    execution_results: list[dict[str, Any]] = Field(default_factory=list)


class PipelineStageResult(BaseModel):
    stage: str
    items_processed: int = 0
    duration_ms: float = 0.0
    error_count: int = 0


class DigestReport(BaseModel):
    generated_at: str
    mode: Mode
    total_notes: int
    stale_notes: int
    labile_notes: int
    missing_source_notes: int
    promotion_candidates: int = 0
    recent_promotions: int = 0
    top_risks: list[str] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)
    pipeline_stages: list[PipelineStageResult] = Field(default_factory=list)


class ChangeSet(BaseModel):
    changed_paths: list[str] = Field(default_factory=list)
    recent_commits: list[str] = Field(default_factory=list)
    mode: Mode = Mode.PHASIC
