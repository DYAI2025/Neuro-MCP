from __future__ import annotations

from datetime import datetime, timedelta, timezone

try:
    from datetime import UTC
except ImportError:
    UTC = timezone.utc

from neuro_mcp.models import FreshnessState, NoteMetadata, NoteStatus
from neuro_mcp.synaptic_tagging import evaluate_promotions


def test_promote_inbox_with_code_correlation():
    note = NoteMetadata(
        note_id="n1",
        title="RingStory Idea",
        path="/brain/80-inbox/idea.md",
        note_type="inbox",
        decay_class="7d",
        status=NoteStatus.ACTIVE,
        created=datetime.now(UTC) - timedelta(hours=12),
        linked_paths=["src/ring_story.py"],
        source_precision=0.4,
    )
    changed_files = {"src/ring_story.py", "src/other.py"}

    promotions = evaluate_promotions(
        notes={"n1": note},
        changed_files=changed_files,
        stc_window_hours=48,
    )
    assert len(promotions) == 1
    assert promotions[0]["note_id"] == "n1"
    assert promotions[0]["new_decay_class"] == "30d"


def test_no_promote_old_inbox():
    note = NoteMetadata(
        note_id="n2",
        title="Old Idea",
        path="/brain/80-inbox/old.md",
        note_type="inbox",
        decay_class="7d",
        status=NoteStatus.ACTIVE,
        created=datetime.now(UTC) - timedelta(hours=72),
        linked_paths=["src/ring_story.py"],
        source_precision=0.4,
    )
    promotions = evaluate_promotions(
        notes={"n2": note},
        changed_files={"src/ring_story.py"},
        stc_window_hours=48,
    )
    assert len(promotions) == 0


def test_no_promote_non_inbox():
    note = NoteMetadata(
        note_id="n3",
        title="Architecture",
        path="/brain/10-architecture/sys.md",
        note_type="architecture-doc",
        decay_class="90d",
        status=NoteStatus.ACTIVE,
        created=datetime.now(UTC) - timedelta(hours=1),
        linked_paths=["src/ring_story.py"],
        source_precision=0.9,
    )
    promotions = evaluate_promotions(
        notes={"n3": note},
        changed_files={"src/ring_story.py"},
        stc_window_hours=48,
    )
    assert len(promotions) == 0


def test_no_promote_without_linked_paths():
    note = NoteMetadata(
        note_id="n4",
        title="Random Idea",
        path="/brain/80-inbox/random.md",
        note_type="inbox",
        decay_class="7d",
        status=NoteStatus.ACTIVE,
        created=datetime.now(UTC) - timedelta(hours=1),
        linked_paths=[],
        source_precision=0.3,
    )
    promotions = evaluate_promotions(
        notes={"n4": note},
        changed_files={"src/something.py"},
        stc_window_hours=48,
    )
    assert len(promotions) == 0


def test_no_promote_no_overlap():
    note = NoteMetadata(
        note_id="n5",
        title="UI Idea",
        path="/brain/80-inbox/ui.md",
        note_type="inbox",
        decay_class="7d",
        status=NoteStatus.ACTIVE,
        created=datetime.now(UTC) - timedelta(hours=5),
        linked_paths=["src/frontend.tsx"],
        source_precision=0.4,
    )
    promotions = evaluate_promotions(
        notes={"n5": note},
        changed_files={"src/backend.py"},
        stc_window_hours=48,
    )
    assert len(promotions) == 0
