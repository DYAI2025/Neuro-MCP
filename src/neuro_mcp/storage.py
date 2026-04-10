from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Iterable

from .models import DocKind, DocumentRecord


SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    doc_id TEXT PRIMARY KEY,
    kind TEXT NOT NULL,
    owner_id TEXT NOT NULL,
    path TEXT NOT NULL,
    uri TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    snippet TEXT NOT NULL,
    line_start INTEGER NOT NULL,
    line_end INTEGER NOT NULL,
    content_hash TEXT NOT NULL,
    metadata_json TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_documents_kind ON documents(kind);
CREATE INDEX IF NOT EXISTS idx_documents_owner_id ON documents(owner_id);
CREATE INDEX IF NOT EXISTS idx_documents_path ON documents(path);
"""


class Repository:
    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(str(self.db_path))
        connection.row_factory = sqlite3.Row
        return connection

    def _init(self) -> None:
        with self._connect() as conn:
            conn.executescript(SCHEMA)

    def replace_kind(self, kind: DocKind, documents: Iterable[DocumentRecord]) -> None:
        docs = list(documents)
        with self._connect() as conn:
            conn.execute("DELETE FROM documents WHERE kind = ?", (kind.value,))
            conn.executemany(
                """
                INSERT INTO documents (
                    doc_id, kind, owner_id, path, uri, title, content, snippet,
                    line_start, line_end, content_hash, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        doc.doc_id,
                        doc.kind.value,
                        doc.owner_id,
                        doc.path,
                        doc.uri,
                        doc.title,
                        doc.content,
                        doc.snippet,
                        doc.line_start,
                        doc.line_end,
                        doc.content_hash,
                        json.dumps(doc.metadata, ensure_ascii=True),
                    )
                    for doc in docs
                ],
            )

    def all_documents(self, kind: DocKind | None = None) -> list[DocumentRecord]:
        with self._connect() as conn:
            if kind is None:
                rows = conn.execute("SELECT * FROM documents ORDER BY kind, path, line_start").fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM documents WHERE kind = ? ORDER BY path, line_start",
                    (kind.value,),
                ).fetchall()
        return [self._row_to_document(row) for row in rows]

    @staticmethod
    def _row_to_document(row: sqlite3.Row) -> DocumentRecord:
        return DocumentRecord(
            doc_id=row["doc_id"],
            kind=DocKind(row["kind"]),
            owner_id=row["owner_id"],
            path=row["path"],
            uri=row["uri"],
            title=row["title"],
            content=row["content"],
            snippet=row["snippet"],
            line_start=row["line_start"],
            line_end=row["line_end"],
            content_hash=row["content_hash"],
            metadata=json.loads(row["metadata_json"]),
        )
