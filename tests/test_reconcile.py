from neuro_mcp.models import DocKind, Mode, SearchResult
from neuro_mcp.reconcile import reconcile_results


def _brain_result() -> SearchResult:
    return SearchResult(
        kind=DocKind.BRAIN,
        owner_id="note-1",
        path="/tmp/note.md",
        title="Tech Stack",
        snippet="We use prisma and postgres",
        uri="brain://note-1",
        relevance=0.9,
        lexical_score=0.8,
        semantic_score=0.9,
        freshness="current",
        status="active",
        source_precision=0.9,
        last_verified="2026-04-10",
        source_files_exist=True,
        metadata={"claimed_dependencies": ["prisma"], "source_files_exist": True, "status": "active"},
    )


def _code_result() -> SearchResult:
    return SearchResult(
        kind=DocKind.CODE,
        owner_id="package.json",
        path="/tmp/package.json",
        title="package.json",
        snippet='{"dependencies":{"next":"15.0.0"}}',
        uri="code://package.json",
        relevance=0.7,
        lexical_score=0.6,
        semantic_score=0.7,
        freshness="current",
        status="active",
        source_precision=1.0,
        last_verified="2026-04-10",
        source_files_exist=True,
        metadata={},
    )


def test_reconcile_prefers_code_on_manifest_conflict() -> None:
    report = reconcile_results(
        query="Are we using prisma?",
        brain_results=[_brain_result()],
        code_results=[_code_result()],
        manifests={"package.json": {"next"}},
        mode=Mode.PHASIC,
    )
    assert report.source_of_truth == "code"
    assert report.contradictions
