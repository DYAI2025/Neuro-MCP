"""Write brain notes with proper YAML frontmatter."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from datetime import UTC
except ImportError:
    UTC = timezone.utc

from .frontmatter import dump_markdown_note


def write_note(
    brain_root: Path,
    relative_path: str,
    title: str,
    content: str,
    note_type: str = "note",
    tags: list[str] | None = None,
    decay_class: str = "30d",
    source_precision: float = 0.7,
    claimed_dependencies: list[str] | None = None,
    extra_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Write or update a note. Returns status dict."""
    full_path = (brain_root / relative_path).resolve()
    if not full_path.is_relative_to(brain_root.resolve()):
        raise ValueError(f"Path escapes outside brain root: {relative_path}")
    existed = full_path.exists()

    metadata: dict[str, Any] = {
        "title": title,
        "type": note_type,
        "status": "active",
        "tags": tags or [],
        "decay_class": decay_class,
        "source_precision": source_precision,
        "last_verified": datetime.now(UTC).strftime("%Y-%m-%d"),
    }
    if not existed:
        metadata["created"] = datetime.now(UTC).strftime("%Y-%m-%d")
    if claimed_dependencies:
        metadata["claimed_dependencies"] = claimed_dependencies
    if extra_metadata:
        metadata.update(extra_metadata)

    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(dump_markdown_note(metadata, content), encoding="utf-8")

    return {
        "status": "updated" if existed else "created",
        "path": relative_path,
        "title": title,
    }
