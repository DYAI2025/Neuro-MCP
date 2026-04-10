from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

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
