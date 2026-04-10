"""File system watcher with debounce for auto-reindexing."""
from __future__ import annotations

import asyncio

from .service import NeuroMCPService


async def watch_forever(
    service: NeuroMCPService,
    debounce_seconds: float = 5.0,
) -> None:
    """Watch brain and code roots, re-index on changes with debounce."""
    from watchfiles import awatch

    roots = [service.settings.brain_root, service.settings.code_root]
    async for _changes in awatch(*roots, debounce=int(debounce_seconds * 1000)):
        service.refresh()
        await asyncio.sleep(0)
