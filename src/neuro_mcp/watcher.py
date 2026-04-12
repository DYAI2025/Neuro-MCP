"""File system watcher with debounce for auto-reindexing and agent dispatch."""
from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from watchfiles import Change, awatch

from .service import NeuroMCPService

logger = logging.getLogger(__name__)

# Map watchfiles Change enum to event types the dispatcher understands
_CHANGE_MAP = {
    Change.added: "created",
    Change.modified: "modified",
    Change.deleted: "deleted",
}


async def watch_forever(
    service: NeuroMCPService,
    debounce_seconds: float = 5.0,
) -> None:
    """Watch brain and code roots, dispatch agents and re-index on changes.

    For each file change:
    1. If the file is in brain_root → dispatch to agent (intake or verify)
    2. Then run service.refresh() to re-index

    refresh() is CPU- and I/O-heavy (file reads, SQL writes, TF-IDF fit).
    It is dispatched to a thread pool via run_in_executor so the event loop
    stays responsive to MCP/HTTP requests during re-indexing.
    """
    loop = asyncio.get_running_loop()
    roots = [service.settings.brain_root, service.settings.code_root]

    # Get the dispatcher if agents are configured
    dispatcher = getattr(service, "_agent_dispatcher", None)

    async for changes in awatch(*roots, debounce=int(debounce_seconds * 1000)):
        # Phase 1: Dispatch agents for individual file events
        if dispatcher:
            code_changes = []
            for change_type, path_str in changes:
                path = Path(path_str)
                event = _CHANGE_MAP.get(change_type, "modified")

                try:
                    if _is_under(path, service.settings.brain_root):
                        # Brain file → dispatch intake or verify agent
                        await loop.run_in_executor(
                            None, dispatcher.on_file_event, path, event
                        )
                    elif _is_under(path, service.settings.code_root):
                        code_changes.append(path_str)
                except Exception:
                    logger.exception("Agent dispatch failed for %s", path_str)

            # Code changes → reconcile agent (batched)
            if code_changes:
                try:
                    await loop.run_in_executor(
                        None, dispatcher.on_code_change, code_changes
                    )
                except Exception:
                    logger.exception("Reconcile dispatch failed")

        # Phase 2: Re-index (always, regardless of agents)
        try:
            await loop.run_in_executor(None, service.refresh)
        except Exception:
            logger.exception("Error during auto-refresh after file change")


def _is_under(path: Path, root: Path) -> bool:
    """Check if path is under root, handling symlinks gracefully."""
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False
