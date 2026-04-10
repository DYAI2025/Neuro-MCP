"""Test that frontmatter parser handles Windows CRLF line endings."""
from __future__ import annotations

from pathlib import Path
from neuro_mcp.frontmatter import parse_markdown_note


def test_parse_crlf_frontmatter(tmp_path: Path):
    note = tmp_path / "note.md"
    note.write_bytes(b"---\r\ntitle: hello\r\n---\r\n\r\nBody text")
    meta, body = parse_markdown_note(note)
    assert meta.get("title") == "hello"
    assert "Body" in body
