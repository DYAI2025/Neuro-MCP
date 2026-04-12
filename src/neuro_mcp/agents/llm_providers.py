"""LLM Provider abstraction — makes agents work with any LLM.

Supported providers:
- anthropic: Claude via Anthropic API
- openai: GPT-4/etc. via OpenAI API (also works for OpenRouter, Azure)
- ollama: Local models via Ollama HTTP API
- litellm: Universal proxy (if installed)

Users configure which provider to use in their config YAML:

  agents:
    llm_provider: anthropic          # or openai, ollama, litellm
    llm_model: claude-sonnet-4-20250514
    llm_api_key_env: ANTHROPIC_API_KEY
    llm_base_url: null               # override for ollama/openrouter
"""

from __future__ import annotations

import json
import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class LLMConfig:
    """Provider-agnostic LLM configuration."""

    provider: str = "anthropic"  # anthropic | openai | ollama | litellm
    model: str = "claude-sonnet-4-20250514"
    api_key: str | None = None
    api_key_env: str = "ANTHROPIC_API_KEY"
    base_url: str | None = None  # for ollama: http://localhost:11434
    max_tokens: int = 1024
    temperature: float = 0.0

    def resolve_api_key(self) -> str:
        if self.api_key:
            return self.api_key
        key = os.environ.get(self.api_key_env, "")
        if not key and self.provider not in ("ollama",):
            raise ValueError(
                f"No API key: set {self.api_key_env} or agents.llm_api_key in config"
            )
        return key


class LLMProvider(ABC):
    """Abstract LLM provider — all agents talk through this interface."""

    @abstractmethod
    def chat(self, system: str, user: str, *, json_mode: bool = False) -> str:
        """Send a system+user message pair, return the text response."""
        ...

    def chat_json(self, system: str, user: str) -> dict:
        """Chat with JSON response parsing."""
        raw = self.chat(system, user, json_mode=True)
        cleaned = raw.strip()
        # Strip markdown code fences if present
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            lines = [l for l in lines[1:] if not l.strip().startswith("```")]
            cleaned = "\n".join(lines)
        return json.loads(cleaned)


class AnthropicProvider(LLMProvider):
    """Claude via Anthropic SDK."""

    def __init__(self, config: LLMConfig) -> None:
        self.config = config
        self._client = None

    @property
    def client(self):
        if self._client is None:
            try:
                import anthropic
            except ImportError:
                raise ImportError(
                    "anthropic package required. Install: pip install anthropic"
                )
            kwargs: dict[str, Any] = {"api_key": self.config.resolve_api_key()}
            if self.config.base_url:
                kwargs["base_url"] = self.config.base_url
            self._client = anthropic.Anthropic(**kwargs)
        return self._client

    def chat(self, system: str, user: str, *, json_mode: bool = False) -> str:
        response = self.client.messages.create(
            model=self.config.model,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return response.content[0].text


class OpenAIProvider(LLMProvider):
    """GPT-4 etc. via OpenAI SDK. Also works for OpenRouter, Azure, etc."""

    def __init__(self, config: LLMConfig) -> None:
        self.config = config
        self._client = None

    @property
    def client(self):
        if self._client is None:
            try:
                import openai
            except ImportError:
                raise ImportError(
                    "openai package required. Install: pip install openai"
                )
            kwargs: dict[str, Any] = {"api_key": self.config.resolve_api_key()}
            if self.config.base_url:
                kwargs["base_url"] = self.config.base_url
            self._client = openai.OpenAI(**kwargs)
        return self._client

    def chat(self, system: str, user: str, *, json_mode: bool = False) -> str:
        kwargs: dict[str, Any] = {
            "model": self.config.model,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        response = self.client.chat.completions.create(**kwargs)
        return response.choices[0].message.content or ""


class OllamaProvider(LLMProvider):
    """Local models via Ollama HTTP API. No API key needed."""

    def __init__(self, config: LLMConfig) -> None:
        self.config = config
        self.base_url = config.base_url or "http://localhost:11434"

    def chat(self, system: str, user: str, *, json_mode: bool = False) -> str:
        import urllib.request
        import urllib.error

        payload = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": False,
            "options": {
                "temperature": self.config.temperature,
                "num_predict": self.config.max_tokens,
            },
        }
        if json_mode:
            payload["format"] = "json"

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/api/chat",
            data=data,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                return result.get("message", {}).get("content", "")
        except urllib.error.URLError as e:
            raise ConnectionError(
                f"Ollama not reachable at {self.base_url}: {e}"
            ) from e


class LiteLLMProvider(LLMProvider):
    """Universal proxy via litellm — supports 100+ providers."""

    def __init__(self, config: LLMConfig) -> None:
        self.config = config

    def chat(self, system: str, user: str, *, json_mode: bool = False) -> str:
        try:
            import litellm
        except ImportError:
            raise ImportError(
                "litellm package required. Install: pip install litellm"
            )
        kwargs: dict[str, Any] = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
        }
        if self.config.base_url:
            kwargs["api_base"] = self.config.base_url
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        response = litellm.completion(**kwargs)
        return response.choices[0].message.content or ""


# ── Factory ──────────────────────────────────────────────────────────

_PROVIDERS: dict[str, type[LLMProvider]] = {
    "anthropic": AnthropicProvider,
    "openai": OpenAIProvider,
    "ollama": OllamaProvider,
    "litellm": LiteLLMProvider,
}


def create_provider(config: LLMConfig) -> LLMProvider:
    """Create the right LLM provider from config."""
    cls = _PROVIDERS.get(config.provider)
    if cls is None:
        raise ValueError(
            f"Unknown LLM provider '{config.provider}'. "
            f"Available: {', '.join(_PROVIDERS)}"
        )
    logger.info("LLM provider: %s (model: %s)", config.provider, config.model)
    return cls(config)
