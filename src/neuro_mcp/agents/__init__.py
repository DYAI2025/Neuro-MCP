"""Autonomous agents for NeuroMCP brain maintenance.

LLM-agnostic runtime: reads agent definitions from .brain/agents/*.md
and executes them with any configured LLM provider (Anthropic, OpenAI,
Ollama, LiteLLM).

The human writes notes. Everything else happens automatically.
"""

from .brain_agent import BrainAgent, BrainAgentResult, AgentDefinition, load_agent_definitions
from .dispatcher import AgentDispatcher, DispatcherConfig
from .llm_providers import LLMConfig, LLMProvider, create_provider
from .signals import SignalTracker

# Keep old imports for backward compatibility (deprecated)
from .base import BaseAgent, AgentConfig, AgentResult
from .intake import IntakeAgent
from .verify import VerifyAgent

__all__ = [
    # New (brain-native, LLM-agnostic)
    "BrainAgent",
    "BrainAgentResult",
    "AgentDefinition",
    "AgentDispatcher",
    "DispatcherConfig",
    "LLMConfig",
    "LLMProvider",
    "SignalTracker",
    "create_provider",
    "load_agent_definitions",
    # Legacy (deprecated, kept for backward compat)
    "BaseAgent",
    "AgentConfig",
    "AgentResult",
    "IntakeAgent",
    "VerifyAgent",
]
