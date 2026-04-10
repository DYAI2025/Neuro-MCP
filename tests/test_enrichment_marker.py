"""Test the enrichment marker helper: _neuro_mcp_enriched + _neuro_mcp_last."""
from datetime import datetime, timezone

from neuro_mcp.frontmatter import ENRICHMENT_VERSION, stamp_enrichment_marker


def test_stamp_sets_enriched_version():
    meta = {"title": "Test", "type": "note"}
    stamp_enrichment_marker(meta)
    assert meta["_neuro_mcp_enriched"] == ENRICHMENT_VERSION
    assert meta["_neuro_mcp_enriched"] == "v1"


def test_stamp_sets_last_timestamp():
    meta = {}
    stamp_enrichment_marker(meta)
    assert "_neuro_mcp_last" in meta
    ts = meta["_neuro_mcp_last"]
    assert isinstance(ts, str)
    parsed = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    assert parsed.tzinfo is not None


def test_stamp_preserves_existing_fields():
    meta = {"title": "Test", "type": "note", "status": "active", "tags": ["a", "b"]}
    stamp_enrichment_marker(meta)
    assert meta["title"] == "Test"
    assert meta["type"] == "note"
    assert meta["status"] == "active"
    assert meta["tags"] == ["a", "b"]


def test_stamp_updates_timestamp_on_re_enrichment():
    meta = {"_neuro_mcp_enriched": "v1", "_neuro_mcp_last": "2020-01-01T00:00:00Z"}
    stamp_enrichment_marker(meta)
    assert meta["_neuro_mcp_enriched"] == "v1"
    ts = meta["_neuro_mcp_last"]
    parsed = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    assert parsed.year >= 2026


def test_stamp_accepts_explicit_timestamp():
    meta = {}
    fixed = datetime(2026, 4, 10, 12, 0, 0, tzinfo=timezone.utc)
    stamp_enrichment_marker(meta, now=fixed)
    assert meta["_neuro_mcp_last"] == "2026-04-10T12:00:00Z"
