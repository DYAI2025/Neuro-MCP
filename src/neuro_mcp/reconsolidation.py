"""Reconsolidation: mark notes as labile when contradictions are detected."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from datetime import UTC
except ImportError:
    UTC = timezone.utc

from .frontmatter import dump_markdown_note, parse_markdown_note


IMMUTABLE_DECAY_CLASSES = {"immutable"}
IMMUTABLE_TYPES = {"adr"}


def apply_reconsolidation(
    note_path: Path,
    contradictions: list[str],
) -> dict[str, Any]:
    """Mark a note as labile if contradictions exist. Skip immutable notes.

    Does NOT delete or overwrite content — only updates status in frontmatter.
    """
    if not note_path.exists():
        return {"action": "skipped", "reason": "file_not_found", "path": str(note_path)}

    meta, body = parse_markdown_note(note_path)

    decay_class = str(meta.get("decay_class", "30d"))
    note_type = str(meta.get("type", "note")).lower()

    if decay_class in IMMUTABLE_DECAY_CLASSES or note_type in IMMUTABLE_TYPES:
        return {
            "action": "skipped",
            "reason": f"immutable ({decay_class}/{note_type})",
            "path": str(note_path),
        }

    if not contradictions:
        return {"action": "no_action", "reason": "no_contradictions", "path": str(note_path)}

    # Mark labile
    meta["status"] = "labile"
    meta["labile_since"] = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    meta["labile_reasons"] = contradictions[:5]  # cap at 5

    note_path.write_text(dump_markdown_note(meta, body), encoding="utf-8")

    return {
        "action": "marked_labile",
        "path": str(note_path),
        "contradictions": contradictions[:5],
    }
