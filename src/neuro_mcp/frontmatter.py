from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml


FRONTMATTER_RE = re.compile(r"^---\r?\n(.*?)\r?\n---\r?\n(.*)$", re.DOTALL)


def parse_markdown_note(path: str | Path) -> tuple[dict[str, Any], str]:
    text = Path(path).read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}, text
    frontmatter_text, body = match.groups()
    metadata = yaml.safe_load(frontmatter_text) or {}
    if not isinstance(metadata, dict):
        metadata = {}
    return metadata, body


def dump_markdown_note(metadata: dict[str, Any], body: str) -> str:
    frontmatter = yaml.safe_dump(metadata, sort_keys=False, allow_unicode=False).strip()
    return f"---\n{frontmatter}\n---\n\n{body.strip()}\n"
