"""Test that Repository reuses its SQLite connection."""
from __future__ import annotations

from pathlib import Path

from neuro_mcp.storage import Repository


def test_repository_reuses_connection(tmp_path: Path):
    """Multiple operations should reuse the same connection object."""
    repo = Repository(tmp_path / "test.db")
    conn1 = repo._conn
    repo.all_documents()
    conn2 = repo._conn
    assert conn1 is conn2, "Connection should be reused, not recreated"


def test_repository_close_releases_connection(tmp_path: Path):
    """After close(), connection should be None."""
    repo = Repository(tmp_path / "test.db")
    assert repo._conn is not None
    repo.close()
    assert repo._conn is None


def test_repository_operations_after_close(tmp_path: Path):
    """Operations after close() should auto-reconnect."""
    repo = Repository(tmp_path / "test.db")
    repo.close()
    docs = repo.all_documents()
    assert isinstance(docs, list)
    assert repo._conn is not None
