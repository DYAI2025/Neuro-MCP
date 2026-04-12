"""Agent Dispatcher — routes filesystem events to brain-native agents.

Reads agent definitions from .brain/agents/*.md and dispatches events
to the appropriate BrainAgent instance. LLM-agnostic: works with any
provider configured in the agents: block.

Integrates with the file watcher:
- New file → Intake Agent (classify, enrich, move)
- Modified file → Verify Agent (quick: update last_verified)
- Code file changed → queue Reconcile Agent
- Scheduled → GC Agent, Synthesis Agent
"""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .brain_agent import (
    AgentDefinition,
    BrainAgent,
    BrainAgentResult,
    load_agent_definitions,
)
from .llm_providers import LLMConfig, LLMProvider, create_provider
from .signals import SignalTracker

if TYPE_CHECKING:
    from ..service import NeuroMCPService

try:
    from datetime import UTC
except ImportError:
    from datetime import timezone
    UTC = timezone.utc

logger = logging.getLogger(__name__)


@dataclass
class DispatcherConfig:
    """Configuration for the agent dispatcher."""

    enabled: bool = True
    intake_enabled: bool = True
    verify_enabled: bool = True
    reconcile_enabled: bool = True
    gc_enabled: bool = True
    synthesis_enabled: bool = True
    auto_move_to_folder: bool = True
    debounce_seconds: float = 10.0


class AgentDispatcher:
    """Routes filesystem events to brain-native agents.

    This is the LLM-agnostic replacement for the old dispatcher.
    It reads .brain/agents/*.md definitions and uses the configured
    LLM provider (Anthropic, OpenAI, Ollama, etc.) to power them.
    """

    def __init__(
        self,
        brain_root: Path,
        llm_config: LLMConfig,
        dispatcher_config: DispatcherConfig | None = None,
        service: "NeuroMCPService | None" = None,
    ) -> None:
        self.brain_root = brain_root
        self.config = dispatcher_config or DispatcherConfig()
        self.service = service
        self._recent_files: dict[str, float] = {}
        self._lock = threading.Lock()
        self._results: list[BrainAgentResult] = []

        # Core components
        self.signals = SignalTracker(brain_root)
        self._llm_config = llm_config
        self._llm: LLMProvider | None = None  # lazy init

        # Load agent definitions from .brain/agents/
        self._definitions = load_agent_definitions(brain_root)

        # Lazy-init agents per definition
        self._agents: dict[str, BrainAgent] = {}

    @property
    def llm(self) -> LLMProvider:
        """Lazy-init LLM provider (only when first agent needs it)."""
        if self._llm is None:
            self._llm = create_provider(self._llm_config)
        return self._llm

    def _get_agent(self, name: str) -> BrainAgent | None:
        """Get or create a BrainAgent for the given definition name."""
        if name not in self._definitions:
            return None
        if name not in self._agents:
            self._agents[name] = BrainAgent(
                definition=self._definitions[name],
                llm=self.llm,
                brain_root=self.brain_root,
                signals=self.signals,
            )
        return self._agents[name]

    def on_file_event(
        self, path: str | Path, event_type: str = "modified"
    ) -> BrainAgentResult | None:
        """Handle a filesystem event from the watcher."""
        if not self.config.enabled:
            return None

        path = Path(path)

        # Skip non-brain files
        if not self._is_brain_file(path):
            return None

        # Skip dotfiles and hidden dirs (but not .brain/)
        parts = path.relative_to(self.brain_root).parts
        if any(p.startswith(".") and p != ".brain" for p in parts):
            return None

        # Skip .brain/state/ files (our own output)
        if self._is_state_file(path):
            return None

        # Debounce
        with self._lock:
            now = time.time()
            key = str(path)
            last = self._recent_files.get(key, 0)
            if now - last < self.config.debounce_seconds:
                return None
            self._recent_files[key] = now

        # Route to agent
        result = None

        if event_type == "deleted":
            logger.debug("[dispatcher] File deleted: %s — no agent action", path.name)
            return None

        if event_type == "created" and self.config.intake_enabled:
            agent = self._get_agent("intake")
            if agent:
                logger.info("[dispatcher] New file → Intake Agent: %s", path.name)
                result = agent.run_intake(path)

        elif event_type == "modified" and self.config.verify_enabled:
            agent = self._get_agent("verify")
            if agent:
                logger.info("[dispatcher] Modified file → Verify Agent (quick): %s", path.name)
                result = agent.run_verify_quick(path)

        if result:
            self._results.append(result)
            logger.info(
                "[dispatcher] %s → %s (%s)",
                path.name, result.action,
                "ok" if result.success else result.error,
            )

        return result

    def on_code_change(self, changed_files: list[str]) -> list[BrainAgentResult]:
        """Handle code changes. Triggers Reconcile Agent if available."""
        if not self.config.reconcile_enabled:
            return []

        agent = self._get_agent("reconcile")
        if not agent:
            logger.debug("[dispatcher] No reconcile agent definition found")
            return []

        # Norepinephrine: system change detected
        if len(changed_files) > 5:
            self.signals.adjust_system("norepinephrine", 0.2)

        logger.info("[dispatcher] Code changes: %d files — reconcile queued", len(changed_files))
        return []  # Actual reconcile runs via service.reconcile()

    def run_gc(self) -> BrainAgentResult | None:
        """Manually trigger GC agent."""
        if not self.config.gc_enabled:
            return None

        agent = self._get_agent("gc")
        if not agent or not self.service:
            return None

        # Get stale notes from the service
        try:
            gc_report = self.service.gc(dry_run=True)
            stale = [
                {"path": c.path, "reason": c.reason}
                for c in gc_report.candidates
            ]
            total = gc_report.total_notes
        except Exception as e:
            logger.error("[dispatcher] GC failed to get report: %s", e)
            return None

        result = agent.run_gc(stale, total)
        if result:
            self._results.append(result)
        return result

    def recent_results(self, limit: int = 20) -> list[BrainAgentResult]:
        return list(reversed(self._results[-limit:]))

    def signal_snapshot(self) -> dict[str, Any]:
        """Return current neurotransmitter signal levels."""
        return self.signals.snapshot()

    def reload_definitions(self) -> None:
        """Reload agent definitions from disk (hot reload)."""
        self._definitions = load_agent_definitions(self.brain_root)
        self._agents.clear()  # Force re-creation with new definitions
        logger.info("Reloaded %d agent definitions", len(self._definitions))

    def _is_brain_file(self, path: Path) -> bool:
        try:
            path.relative_to(self.brain_root)
            return True
        except ValueError:
            return False

    def _is_state_file(self, path: Path) -> bool:
        """Check if path is inside .brain/state/ (our own output)."""
        try:
            rel = path.relative_to(self.brain_root / ".brain" / "state")
            return True
        except ValueError:
            return False

    def _is_code_file(self, path: Path) -> bool:
        """Check if the file is inside code_root (if service available)."""
        if not self.service:
            return False
        try:
            path.relative_to(self.service.settings.code_root)
            return True
        except ValueError:
            return False
