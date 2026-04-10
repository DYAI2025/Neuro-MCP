from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable

from .models import FreshnessState, NoteMetadata, NoteStatus

# UTC compatibility for Python 3.10
try:
    from datetime import UTC
except ImportError:
    UTC = timezone.utc


DECAY_DAYS = {
    "immutable": None,
    "90d": 90,
    "60d": 60,
    "30d": 30,
    "14d": 14,
    "7d": 7,
}


TYPE_DEFAULT_DECAY = {
    "adr": "immutable",
    "architecture-doc": "90d",
    "architecture": "90d",
    "tech": "60d",
    "component": "30d",
    "api-doc": "30d",
    "bug": "14d",
    "bug-fix": "14d",
    "workflow": "30d",
    "inbox": "7d",
    "note": "30d",
}


@dataclass(slots=True)
class FreshnessComputation:
    freshness: FreshnessState
    stale_reasons: list[str]
    recommended_status: NoteStatus


def _now() -> datetime:
    return datetime.now(UTC)


def decay_days_for(note_type: str, decay_class: str | None) -> int | None:
    if decay_class:
        return DECAY_DAYS.get(decay_class, None)
    return DECAY_DAYS.get(TYPE_DEFAULT_DECAY.get(note_type, "30d"))


def compute_freshness(
    note_type: str,
    decay_class: str | None,
    last_verified: datetime | None,
    source_files_exist: bool,
    immutable_note_types: Iterable[str] = ("adr",),
) -> FreshnessComputation:
    if note_type in immutable_note_types or decay_class == "immutable":
        return FreshnessComputation(
            freshness=FreshnessState.IMMUTABLE,
            stale_reasons=[] if source_files_exist else ["linked_source_missing"],
            recommended_status=NoteStatus.ACTIVE if source_files_exist else NoteStatus.LABILE,
        )

    reasons: list[str] = []
    if not source_files_exist:
        reasons.append("linked_source_missing")

    if last_verified is None:
        reasons.append("never_verified")
        return FreshnessComputation(
            freshness=FreshnessState.STALE if source_files_exist else FreshnessState.MISSING_SOURCES,
            stale_reasons=reasons,
            recommended_status=NoteStatus.STALE,
        )

    days = decay_days_for(note_type, decay_class)
    if days is None:
        return FreshnessComputation(
            freshness=FreshnessState.IMMUTABLE,
            stale_reasons=reasons,
            recommended_status=NoteStatus.ACTIVE if not reasons else NoteStatus.LABILE,
        )

    age_days = max(0.0, (_now() - last_verified).total_seconds() / 86400.0)
    if age_days > days:
        reasons.append(f"older_than_{days}d")
        return FreshnessComputation(
            freshness=FreshnessState.STALE if source_files_exist else FreshnessState.MISSING_SOURCES,
            stale_reasons=reasons,
            recommended_status=NoteStatus.STALE,
        )
    if age_days > days * 0.5:
        return FreshnessComputation(
            freshness=FreshnessState.AGING if source_files_exist else FreshnessState.MISSING_SOURCES,
            stale_reasons=reasons,
            recommended_status=NoteStatus.ACTIVE if source_files_exist else NoteStatus.LABILE,
        )
    return FreshnessComputation(
        freshness=FreshnessState.CURRENT if source_files_exist else FreshnessState.MISSING_SOURCES,
        stale_reasons=reasons,
        recommended_status=NoteStatus.ACTIVE if source_files_exist else NoteStatus.LABILE,
    )


def freshness_bonus(value: FreshnessState) -> float:
    if value == FreshnessState.IMMUTABLE:
        return 0.95
    if value == FreshnessState.CURRENT:
        return 1.00
    if value == FreshnessState.AGING:
        return 0.75
    if value == FreshnessState.MISSING_SOURCES:
        return 0.25
    return 0.40
