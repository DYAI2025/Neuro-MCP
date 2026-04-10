from pathlib import Path

from neuro_mcp.frontmatter import dump_markdown_note, parse_markdown_note


def test_frontmatter_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "note.md"
    metadata = {"title": "Example", "tags": ["a", "b"], "last_verified": "2026-04-10"}
    body = "# Example\n\nSome content."
    path.write_text(dump_markdown_note(metadata, body), encoding="utf-8")

    parsed_metadata, parsed_body = parse_markdown_note(path)
    assert parsed_metadata["title"] == "Example"
    assert parsed_metadata["tags"] == ["a", "b"]
    assert "Some content." in parsed_body
