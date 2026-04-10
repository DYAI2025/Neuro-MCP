from __future__ import annotations

from pathlib import Path

from .freshness import compute_freshness
from .models import GarbageCollectionItem, GarbageCollectionReport, Mode, NoteStatus


def build_gc_report(notes: list[dict], mode: Mode, dry_run: bool) -> GarbageCollectionReport:
    items: list[GarbageCollectionItem] = []
    stale_count = 0
    missing_sources_count = 0
    archived_candidates = 0

    for note in notes:
        note_type = note.get("note_type", "note")
        decay_class = note.get("decay_class", "30d")
        last_verified = note.get("last_verified")
        source_files_exist = bool(note.get("source_files_exist", True))
        status_before_raw = note.get("status", "active")
        status_before = getattr(status_before_raw, "value", str(status_before_raw))

        freshness = compute_freshness(
            note_type=note_type,
            decay_class=decay_class,
            last_verified=last_verified,
            source_files_exist=source_files_exist,
        )
        status_after = freshness.recommended_status.value
        reason = ", ".join(freshness.stale_reasons) or freshness.freshness.value

        if freshness.freshness.value in {"stale", "missing_sources"}:
            stale_count += 1
        if freshness.freshness.value == "missing_sources":
            missing_sources_count += 1

        action = "keep"
        if note_type == "inbox" and freshness.freshness.value in {"stale", "missing_sources"}:
            action = "archive_candidate"
            archived_candidates += 1
        elif note_type in {"bug", "bug-fix"} and freshness.freshness.value == "stale":
            action = "archive_candidate"
            archived_candidates += 1
        elif status_before != status_after:
            action = "update_status"

        if action != "keep":
            items.append(
                GarbageCollectionItem(
                    note_id=str(note.get("note_id")),
                    path=str(note.get("path")),
                    action=action if dry_run else action.replace("_candidate", ""),
                    reason=reason,
                    status_before=status_before,
                    status_after=status_after,
                )
            )

    return GarbageCollectionReport(
        dry_run=dry_run,
        mode=mode,
        items=items,
        total_notes=len(notes),
        stale_count=stale_count,
        missing_sources_count=missing_sources_count,
        archived_candidates=archived_candidates,
    )


def execute_gc_actions(
    items: list[GarbageCollectionItem],
    backup_dir: Path | None = None,
) -> list[dict]:
    """Execute GC actions by updating frontmatter on disk. Creates backups."""
    import shutil
    from datetime import datetime, timezone

    try:
        from datetime import UTC
    except ImportError:
        UTC = timezone.utc

    from .frontmatter import dump_markdown_note, parse_markdown_note

    results = []
    for item in items:
        path = Path(item.path)
        if not path.exists():
            results.append({"note_id": item.note_id, "executed": False, "reason": "file_not_found"})
            continue

        # Backup
        if backup_dir:
            backup_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, backup_dir / path.name)

        meta, body = parse_markdown_note(path)
        meta["status"] = item.status_after
        if item.status_after == "archived":
            meta["archived_at"] = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        path.write_text(dump_markdown_note(meta, body), encoding="utf-8")
        results.append({"note_id": item.note_id, "executed": True, "status_after": item.status_after})

    return results
