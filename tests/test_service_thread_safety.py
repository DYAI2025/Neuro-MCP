# tests/test_service_thread_safety.py
"""Test that concurrent refresh() + search() calls don't corrupt state."""
from __future__ import annotations

import threading
import time
from pathlib import Path

import pytest

from neuro_mcp.config import Settings
from neuro_mcp.service import NeuroMCPService


@pytest.fixture
def svc(tmp_path: Path) -> NeuroMCPService:
    brain = tmp_path / "brain"
    brain.mkdir()
    code = tmp_path / "code"
    code.mkdir()
    (brain / "note.md").write_text(
        "---\ntitle: Test\nlast_verified: 2026-04-10\n---\nContent about testing.",
        encoding="utf-8",
    )
    settings = Settings(brain_root=brain, code_root=code, data_dir=tmp_path / "data")
    return NeuroMCPService(settings)


def test_concurrent_refresh_and_search_do_not_raise(svc: NeuroMCPService):
    """refresh() and search_brain() running concurrently must not raise or deadlock."""
    errors: list[Exception] = []

    def do_refresh():
        for _ in range(20):
            try:
                svc.refresh()
            except Exception as exc:
                errors.append(exc)
            time.sleep(0.001)

    def do_search():
        for _ in range(50):
            try:
                svc.search_brain("testing", top_k=3)
            except Exception as exc:
                errors.append(exc)
            time.sleep(0.001)

    threads = [
        threading.Thread(target=do_refresh),
        threading.Thread(target=do_refresh),
        threading.Thread(target=do_search),
        threading.Thread(target=do_search),
        threading.Thread(target=do_search),
        threading.Thread(target=do_search),
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=10)

    assert not errors, f"Concurrent errors: {errors}"
