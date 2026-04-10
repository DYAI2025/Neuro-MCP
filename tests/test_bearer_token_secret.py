"""Test that bearer_token uses SecretStr and doesn't leak in repr/str."""
from __future__ import annotations

from pydantic import SecretStr
from neuro_mcp.config import Settings


def test_bearer_token_is_secret_str():
    s = Settings(brain_root="/tmp/b", code_root="/tmp/c", bearer_token="super-secret-123")
    assert isinstance(s.bearer_token, SecretStr)


def test_bearer_token_hidden_in_repr():
    s = Settings(brain_root="/tmp/b", code_root="/tmp/c", bearer_token="super-secret-123")
    text = repr(s)
    assert "super-secret-123" not in text


def test_bearer_token_get_secret_value():
    s = Settings(brain_root="/tmp/b", code_root="/tmp/c", bearer_token="super-secret-123")
    assert s.bearer_token.get_secret_value() == "super-secret-123"


def test_bearer_token_none_by_default():
    s = Settings(brain_root="/tmp/b", code_root="/tmp/c")
    assert s.bearer_token is None
