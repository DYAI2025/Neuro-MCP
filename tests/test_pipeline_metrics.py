"""Test PipelineStageResult model and metric recording."""
from neuro_mcp.models import PipelineStageResult


def test_pipeline_stage_result_fields():
    r = PipelineStageResult(
        stage="stc",
        items_processed=3,
        duration_ms=12.5,
        error_count=0,
    )
    assert r.stage == "stc"
    assert r.items_processed == 3
    assert r.duration_ms == 12.5
    assert r.error_count == 0


def test_pipeline_stage_result_defaults():
    r = PipelineStageResult(stage="labile")
    assert r.items_processed == 0
    assert r.duration_ms == 0.0
    assert r.error_count == 0
