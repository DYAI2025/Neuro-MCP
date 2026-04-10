"""Synaptic tagging: promote inbox notes when correlated code changes occur within a time window."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

try:
    from datetime import UTC
except ImportError:
    UTC = timezone.utc

from .models import NoteMetadata


def evaluate_promotions(
    notes: dict[str, NoteMetadata],
    changed_files: set[str],
    stc_window_hours: int = 48,
) -> list[dict[str, Any]]:
    """Evaluate inbox notes for promotion based on code change correlation.

    An inbox note (decay_class=7d) is promoted to 30d if:
    1. It is of type "inbox"
    2. It was created within the last ``stc_window_hours``
    3. Its ``linked_paths`` or ``claimed_dependencies`` overlap with ``changed_files``
    """
    now = datetime.now(UTC)
    promotions: list[dict[str, Any]] = []

    for note_id, note in notes.items():
        if note.note_type != "inbox":
            continue
        if note.decay_class != "7d":
            continue
        if note.created is None:
            continue

        age_hours = (now - note.created).total_seconds() / 3600.0
        if age_hours > stc_window_hours:
            continue

        linked = set(note.linked_paths) | set(note.claimed_dependencies)
        if not linked:
            continue

        overlap = linked & changed_files
        if overlap:
            promotions.append({
                "note_id": note_id,
                "title": note.title,
                "path": note.path,
                "old_decay_class": "7d",
                "new_decay_class": "30d",
                "reason": f"Correlated with code changes: {', '.join(sorted(overlap))}",
                "age_hours": round(age_hours, 1),
            })

    return promotions
