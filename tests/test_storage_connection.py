"""Test that Repository reuses its SQLite connection per thread."""
from __future__ import annotations

from pathlib import Path

from neuro_mcp.storage import Repository


def test_repository_reuses_connection(tmp_path: Path):
    """Multiple operations on the same thread should reuse the same connection."""
    repo = Repository(tmp_path / "test.db")
    conn1 = repo._get_conn()
    repo.all_documents()
    conn2 = repo._get_conn()
    assert conn1 is conn2, "Connection should be reused, not recreated"


def test_repository_close_releases_connection(tmp_path: Path):
    """After close(), the thread-local cache should be empty."""
    repo = Repository(tmp_path / "test.db")
    # Prime a connection on this thread.
    first_conn = repo._get_conn()
    assert first_conn is not None
    repo.close()
    # After close, the thread-local cache should no longer hold the old conn.
    assert getattr(repo._local, "conn", None) is None
    assert repo._all_connections == []


def test_repository_operations_after_close(tmp_path: Path):
    """Operations after close() should auto-reconnect with a fresh connection."""
    repo = Repository(tmp_path / "test.db")
    first_conn = repo._get_conn()
    repo.close()
    docs = repo.all_documents()
    assert isinstance(docs, list)
    new_conn = repo._get_conn()
    assert new_conn is not None
    assert new_conn is not first_conn, "Expected a fresh connection after close"
