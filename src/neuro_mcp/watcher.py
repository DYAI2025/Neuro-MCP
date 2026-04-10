"""File system watcher with debounce for auto-reindexing."""
from __future__ import annotations

import asyncio
import logging

from watchfiles import awatch

from .service import NeuroMCPService

logger = logging.getLogger(__name__)


async def watch_forever(
    service: NeuroMCPService,
    debounce_seconds: float = 5.0,
) -> None:
    """Watch brain and code roots, re-index on changes with debounce.

    refresh() is CPU- and I/O-heavy (file reads, SQL writes, TF-IDF fit).
    It is dispatched to a thread pool via run_in_executor so the event loop
    stays responsive to MCP/HTTP requests during re-indexing.
    """
    loop = asyncio.get_running_loop()
    roots = [service.settings.brain_root, service.settings.code_root]
    async for _changes in awatch(*roots, debounce=int(debounce_seconds * 1000)):
        try:
            await loop.run_in_executor(None, service.refresh)
        except Exception:
            logger.exception("Error during auto-refresh after file change")
