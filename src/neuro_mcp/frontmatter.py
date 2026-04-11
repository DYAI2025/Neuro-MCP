from __future__ import annotations

import re
from datetime import date, datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

if TYPE_CHECKING:
    from .config import FolderTypeRule

try:
    from datetime import UTC
except ImportError:
    UTC = timezone.utc


FRONTMATTER_RE = re.compile(r"^---\r?\n(.*?)\r?\n---\r?\n(.*)$", re.DOTALL)


ENRICHMENT_VERSION = "v1"


def stamp_enrichment_marker(metadata: dict[str, Any], now: datetime | None = None) -> None:
    """Mark metadata as enriched by NeuroMCP.

    Sets `_neuro_mcp_enriched` to the current enrichment schema version and
    `_neuro_mcp_last` to an ISO-8601 UTC timestamp. Mutates the dict in place.
    Existing fields are preserved.
    """
    when = now if now is not None else datetime.now(UTC)
    metadata["_neuro_mcp_enriched"] = ENRICHMENT_VERSION
    metadata["_neuro_mcp_last"] = when.strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_markdown_note(path: str | Path) -> tuple[dict[str, Any], str]:
    text = Path(path).read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}, text
    frontmatter_text, body = match.groups()
    try:
        metadata = yaml.safe_load(frontmatter_text) or {}
    except yaml.YAMLError:
        # Malformed frontmatter (e.g. template placeholders like {{title}})
        return {}, text
    if not isinstance(metadata, dict):
        metadata = {}
    return metadata, body


def dump_markdown_note(metadata: dict[str, Any], body: str) -> str:
    frontmatter = yaml.safe_dump(metadata, sort_keys=False, allow_unicode=False).strip()
    return f"---\n{frontmatter}\n---\n\n{body.strip()}\n"


def _title_from_filename(path: Path) -> str:
    return path.stem.replace("-", " ").replace("_", " ").title()


def enrich_note_frontmatter(
    note_path: Path,
    rule: FolderTypeRule | None,
    today: date | None = None,
) -> bool:
    """Add missing frontmatter fields to a note file.

    Fills in `title`, `type`, `status`, `decay_class`, `last_verified`, and
    `created` only when they are not already set. Existing fields are never
    overwritten (DEC-two-stage-mutations: status-level mutations only, body
    content is never touched).

    If `rule` is provided, it supplies `type` and `decay_class` defaults.
    If `rule` is None, defaults are `type: note, decay_class: 30d`.

    The enrichment marker (`_neuro_mcp_enriched`, `_neuro_mcp_last`) is stamped
    only when the file is actually modified — avoiding spurious timestamp
    churn on already-complete notes.

    Returns True if the note was modified, False otherwise.
    """
    meta, body = parse_markdown_note(note_path)
    changed = False

    when = today if today is not None else date.today()
    today_str = when.strftime("%Y-%m-%d")

    type_val = rule.type if rule is not None else "note"
    decay_val = rule.decay_class if rule is not None else "30d"

    defaults: dict[str, Any] = {
        "title": _title_from_filename(note_path),
        "type": type_val,
        "status": "active",
        "decay_class": decay_val,
        "last_verified": today_str,
        "created": today_str,
    }

    for key, value in defaults.items():
        if key not in meta:
            meta[key] = value
            changed = True

    if changed:
        stamp_enrichment_marker(meta)
        note_path.write_text(dump_markdown_note(meta, body), encoding="utf-8")
    return changed
