from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

# UTC compatibility for Python 3.10
try:
    from datetime import UTC
except ImportError:
    UTC = timezone.utc

from .config import Settings
from .freshness import TYPE_DEFAULT_DECAY, compute_freshness
from .frontmatter import parse_markdown_note
from .models import DocKind, DocumentRecord, NoteMetadata, NoteStatus
from .text_utils import make_snippet, normalize_text, stable_id


def _parse_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.astimezone(UTC)
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day, tzinfo=UTC)
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None
        if len(value) == 10:
            value = value + "T00:00:00+00:00"
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)
        except ValueError:
            return None
    return None


def _guess_note_type(path: Path, metadata: dict[str, Any]) -> str:
    note_type = str(metadata.get("type") or "").strip().lower()
    if note_type:
        return note_type
    folder = path.parts[0].lower() if path.parts else ""
    if "decision" in folder or folder.startswith("20-"):
        return "adr"
    if "architecture" in folder or folder.startswith("10-"):
        return "architecture-doc"
    if "bug" in folder:
        return "bug"
    if "inbox" in folder or folder.startswith("80-"):
        return "inbox"
    return "note"


def _coerce_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, (list, tuple, set)):
        return [str(item) for item in value if str(item).strip()]
    return []


def _split_sections(body: str) -> list[tuple[str, int, int, str]]:
    lines = body.splitlines()
    if not lines:
        return [("body", 1, 1, body)]

    sections: list[tuple[str, int, int, str]] = []
    current_title = "body"
    current_start = 1
    buffer: list[str] = []
    for index, line in enumerate(lines, start=1):
        if line.startswith("#") and buffer:
            sections.append((current_title, current_start, index - 1, "\n".join(buffer).strip()))
            current_title = line.lstrip("#").strip() or "section"
            current_start = index
            buffer = [line]
        else:
            if line.startswith("#") and not buffer:
                current_title = line.lstrip("#").strip() or "section"
                current_start = index
            buffer.append(line)
    if buffer:
        sections.append((current_title, current_start, len(lines), "\n".join(buffer).strip()))
    return [section for section in sections if section[3].strip()]


def scan_brain_documents(settings: Settings) -> tuple[list[DocumentRecord], dict[str, NoteMetadata]]:
    root = settings.brain_root
    documents: list[DocumentRecord] = []
    notes: dict[str, NoteMetadata] = {}

    for path in sorted(root.rglob("*.md")):
        if not path.resolve().is_relative_to(root.resolve()):
            continue
        rel_path = path.relative_to(root)
        metadata_raw, body = parse_markdown_note(path)
        note_type = _guess_note_type(rel_path, metadata_raw)

        linked_paths = _coerce_list(
            metadata_raw.get("linked_paths")
            or metadata_raw.get("source_files")
            or metadata_raw.get("source_paths")
        )
        source_files_exist = all((settings.code_root / linked_path).exists() for linked_path in linked_paths) if linked_paths else True

        decay_class = str(metadata_raw.get("decay_class") or TYPE_DEFAULT_DECAY.get(note_type, "30d"))
        created = _parse_datetime(metadata_raw.get("created"))
        last_verified = _parse_datetime(metadata_raw.get("last_verified"))
        source_precision = float(metadata_raw.get("source_precision", 0.5))

        freshness = compute_freshness(
            note_type=note_type,
            decay_class=decay_class,
            last_verified=last_verified,
            source_files_exist=source_files_exist,
            immutable_note_types=settings.immutable_note_types,
        )

        note_id = stable_id("note", rel_path.as_posix())
        note = NoteMetadata(
            note_id=note_id,
            title=str(metadata_raw.get("title") or rel_path.stem),
            path=str(path),
            note_type=note_type,
            status=NoteStatus(str(metadata_raw.get("status") or freshness.recommended_status.value)),
            created=created,
            last_verified=last_verified,
            decay_class=decay_class,
            source_precision=source_precision,
            source_type=str(metadata_raw.get("source_type") or "manual"),
            tags=_coerce_list(metadata_raw.get("tags")),
            linked_paths=linked_paths,
            claimed_dependencies=_coerce_list(metadata_raw.get("claimed_dependencies")),
            linked_commits=_coerce_list(metadata_raw.get("linked_commits")),
            superseded_by=metadata_raw.get("superseded_by"),
            source_files_exist=source_files_exist,
            freshness=freshness.freshness,
            stale_reasons=freshness.stale_reasons,
            extra={k: v for k, v in metadata_raw.items() if k not in {
                "title", "type", "status", "created", "last_verified", "decay_class",
                "source_precision", "source_type", "tags", "linked_paths",
                "source_files", "source_paths", "claimed_dependencies",
                "linked_commits", "superseded_by"
            }},
        )
        notes[note_id] = note

        sections = _split_sections(body)
        for title, line_start, line_end, section_text in sections:
            doc_id = stable_id("brain", rel_path.as_posix(), title, str(line_start), str(line_end))
            documents.append(
                DocumentRecord(
                    doc_id=doc_id,
                    kind=DocKind.BRAIN,
                    owner_id=note_id,
                    path=str(path),
                    uri=f"brain://{rel_path.as_posix()}#L{line_start}-L{line_end}",
                    title=note.title if title == "body" else f"{note.title} :: {title}",
                    content=section_text,
                    snippet=make_snippet(section_text),
                    line_start=line_start,
                    line_end=line_end,
                    content_hash=stable_id(rel_path.as_posix(), normalize_text(section_text)),
                    metadata=note.model_dump(mode="json"),
                )
            )

    return documents, notes
