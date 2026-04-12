"""Base class for all NeuroMCP agents.

An agent is an autonomous unit that uses an LLM to make decisions about
brain maintenance. Each agent:
1. Receives a trigger (file event, schedule, or explicit call)
2. Gathers context (note content, related notes, code state)
3. Asks the LLM for a decision
4. Executes the decision (write frontmatter, move file, set links, etc.)
"""

from __future__ import annotations

import json
import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..config import Settings

try:
    from datetime import UTC
except ImportError:
    UTC = timezone.utc

logger = logging.getLogger(__name__)


@dataclass
class AgentResult:
    """Outcome of a single agent run."""

    agent: str
    success: bool
    action_taken: str  # e.g. "classified as project", "set labile", "no action"
    details: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class AgentConfig:
    """LLM and agent-level settings, loaded from the agents: block in config."""

    llm_model: str = "claude-sonnet-4-20250514"
    llm_api_key: str | None = None
    llm_api_key_env: str = "ANTHROPIC_API_KEY"
    max_tokens: int = 1024
    temperature: float = 0.0  # deterministic for maintenance tasks

    def resolve_api_key(self) -> str:
        """Get API key from explicit value or environment variable."""
        if self.llm_api_key:
            return self.llm_api_key
        key = os.environ.get(self.llm_api_key_env, "")
        if not key:
            raise ValueError(
                f"No LLM API key: set {self.llm_api_key_env} env var "
                f"or agents.llm_api_key in config"
            )
        return key


class BaseAgent(ABC):
    """Abstract base for all brain-maintenance agents."""

    name: str = "base"

    def __init__(self, settings: Settings, agent_config: AgentConfig) -> None:
        self.settings = settings
        self.agent_config = agent_config
        self._client = None  # lazy init

    @property
    def client(self):
        """Lazy-init the Anthropic client."""
        if self._client is None:
            try:
                import anthropic
            except ImportError:
                raise ImportError(
                    "anthropic package required for agents. "
                    "Install with: pip install anthropic"
                )
            self._client = anthropic.Anthropic(
                api_key=self.agent_config.resolve_api_key()
            )
        return self._client

    def llm_call(self, system: str, user: str) -> str:
        """Make a synchronous LLM call and return the text response."""
        logger.debug("[%s] LLM call: %d chars system, %d chars user",
                     self.name, len(system), len(user))
        response = self.client.messages.create(
            model=self.agent_config.llm_model,
            max_tokens=self.agent_config.max_tokens,
            temperature=self.agent_config.temperature,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        text = response.content[0].text
        logger.debug("[%s] LLM response: %d chars", self.name, len(text))
        return text

    def llm_json(self, system: str, user: str) -> dict:
        """Make an LLM call and parse the response as JSON."""
        raw = self.llm_call(system, user)
        # Strip markdown code fences if present
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            # Remove first and last lines (```json and ```)
            lines = [l for l in lines[1:] if not l.strip().startswith("```")]
            cleaned = "\n".join(lines)
        return json.loads(cleaned)

    @abstractmethod
    def run(self, **kwargs) -> AgentResult:
        """Execute the agent's task. Subclasses must implement."""
        ...
