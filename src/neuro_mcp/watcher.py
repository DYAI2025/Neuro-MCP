"""File system watcher with debounce for auto-reindexing."""
from __future__ import annotations

import asyncio
import logging

from .service import NeuroMCPService

logger = logging.getLogger(__name__)


async def watch_forever(
    service: NeuroMCPService,
    debounce_seconds: float = 5.0,
) -> None:
    """Watch brain and code roots, re-index on changes with debounce."""
    from watchfiles import awatch

    roots = [service.settings.brain_root, service.settings.code_root]
    async for _changes in awatch(*roots, debounce=int(debounce_seconds * 1000)):
        try:
            service.refresh()
        except Exception:
            logger.exception("Error during auto-refresh after file change")
        await asyncio.sleep(0)
