from datetime import datetime, timedelta, timezone

from neuro_mcp.freshness import compute_freshness

# UTC compatibility for Python 3.10
try:
    from datetime import UTC
except ImportError:
    UTC = timezone.utc


def test_stale_after_decay() -> None:
    result = compute_freshness(
        note_type="component",
        decay_class="30d",
        last_verified=datetime.now(UTC) - timedelta(days=45),
        source_files_exist=True,
    )
    assert result.freshness.value == "stale"
    assert result.recommended_status.value == "stale"


def test_immutable_adr() -> None:
    result = compute_freshness(
        note_type="adr",
        decay_class="immutable",
        last_verified=None,
        source_files_exist=True,
    )
    assert result.freshness.value == "immutable"
    assert result.recommended_status.value == "active"
