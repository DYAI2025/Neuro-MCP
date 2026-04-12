from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
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


# ---------------------------------------------------------------------------
# Freeze-on-inactivity: decay only ticks while the system is actively used.
#
# The FreezeTracker persists a heartbeat file in data_dir. On startup it
# detects the gap between now and the last heartbeat, accumulating an
# "offline offset" (timedelta). The effective_now() function subtracts that
# offset from wall-clock time so that notes don't age during downtime.
#
# Heartbeats are written on every search/ingest/refresh call (debounced to
# at most once per minute to avoid disk churn).
# ---------------------------------------------------------------------------

_HEARTBEAT_FILE = "heartbeat.json"
_HEARTBEAT_DEBOUNCE_SECONDS = 60


class FreezeTracker:
    """Tracks cumulative offline time and provides an effective clock."""

    def __init__(self, data_dir: Path | None = None, enabled: bool = True) -> None:
        self.enabled = enabled
        self._data_dir = data_dir
        self._offline_offset = timedelta(0)
        self._last_heartbeat_write: datetime | None = None

        if data_dir and enabled:
            self._load(data_dir)

    def _heartbeat_path(self) -> Path | None:
        return self._data_dir / _HEARTBEAT_FILE if self._data_dir else None

    def _load(self, data_dir: Path) -> None:
        """On startup: read last heartbeat, compute offline gap."""
        hb_path = data_dir / _HEARTBEAT_FILE
        if not hb_path.exists():
            # First run — no gap, write initial heartbeat
            self._write_heartbeat(force=True)
            return

        try:
            raw = json.loads(hb_path.read_text(encoding="utf-8"))
            last_hb = datetime.fromisoformat(raw["last_heartbeat"])
            stored_offset = timedelta(seconds=raw.get("offline_offset_seconds", 0))
        except (json.JSONDecodeError, KeyError, ValueError):
            self._write_heartbeat(force=True)
            return

        now = datetime.now(UTC)
        gap = now - last_hb

        # If the server was offline for more than 5 minutes, count it as
        # inactive time. Short gaps (restarts, deploys) don't freeze.
        grace_minutes = 5
        if gap > timedelta(minutes=grace_minutes):
            inactive_time = gap - timedelta(minutes=grace_minutes)
            self._offline_offset = stored_offset + inactive_time
        else:
            self._offline_offset = stored_offset

        self._write_heartbeat(force=True)

    def heartbeat(self) -> None:
        """Called on active usage. Writes at most once per debounce interval."""
        if not self.enabled or not self._data_dir:
            return
        now = datetime.now(UTC)
        if (
            self._last_heartbeat_write
            and (now - self._last_heartbeat_write).total_seconds() < _HEARTBEAT_DEBOUNCE_SECONDS
        ):
            return
        self._write_heartbeat(force=True)

    def _write_heartbeat(self, force: bool = False) -> None:
        hb_path = self._heartbeat_path()
        if not hb_path:
            return
        now = datetime.now(UTC)
        hb_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "last_heartbeat": now.isoformat(),
            "offline_offset_seconds": self._offline_offset.total_seconds(),
        }
        hb_path.write_text(json.dumps(payload), encoding="utf-8")
        self._last_heartbeat_write = now

    def effective_now(self) -> datetime:
        """Wall-clock time minus accumulated offline time."""
        if not self.enabled:
            return datetime.now(UTC)
        return datetime.now(UTC) - self._offline_offset

    @property
    def offline_offset(self) -> timedelta:
        return self._offline_offset


# Module-level singleton — set by service.py on startup.
_freeze_tracker: FreezeTracker | None = None


def set_freeze_tracker(tracker: FreezeTracker) -> None:
    global _freeze_tracker
    _freeze_tracker = tracker


@dataclass(slots=True)
class FreshnessComputation:
    freshness: FreshnessState
    stale_reasons: list[str]
    recommended_status: NoteStatus


def _now() -> datetime:
    """Return effective time, accounting for freeze-on-inactivity."""
    if _freeze_tracker and _freeze_tracker.enabled:
        return _freeze_tracker.effective_now()
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
