# tests/test_watcher_async.py
"""Test that watch_forever dispatches refresh to a thread pool, not inline."""
from __future__ import annotations

import asyncio
import threading
from unittest.mock import MagicMock, patch

import pytest

from neuro_mcp.watcher import watch_forever


def test_refresh_runs_in_executor():
    """refresh() must not block the event loop — it must be submitted to an executor."""
    service = MagicMock()
    service.settings.brain_root = "/tmp/brain"
    service.settings.code_root = "/tmp/code"

    calls_on_threads: list[str] = []

    def fake_refresh():
        # Record whether we are on the main thread or a worker thread
        calls_on_threads.append(threading.current_thread().name)

    service.refresh.side_effect = fake_refresh

    async def run_one_cycle():
        # Patch awatch to yield exactly one change then stop
        async def fake_awatch(*roots, **kwargs):
            yield {("modified", "/tmp/brain/note.md")}

        with patch("neuro_mcp.watcher.awatch", new=fake_awatch):
            await watch_forever(service, debounce_seconds=0)

    asyncio.run(run_one_cycle())

    # refresh() must have been called
    service.refresh.assert_called_once()
    # It must NOT have run on the main thread (the event loop thread)
    main_thread_name = threading.main_thread().name
    assert all(
        name != main_thread_name for name in calls_on_threads
    ), f"refresh() ran on main thread: {calls_on_threads}"
