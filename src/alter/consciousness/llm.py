"""
LLM Abstraction — Thin wrapper producing think_fn.

The consciousness engine doesn't care which LLM provider is behind
the think_fn. This module provides factory functions to create them.

    think_fn: Callable[[str], str]
        Takes a prompt string, returns raw text. That's it.

Supported providers:
    - "anthropic" → langchain ChatAnthropic
    - "openai"    → langchain ChatOpenAI
    - "mock"      → canned response (for testing)
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)

# Type alias for the think function
ThinkFn = Callable[[str], str]


def create_think_fn(
    provider: str = "anthropic",
    model: Optional[str] = None,
    **kwargs: Any,
) -> ThinkFn:
    """
    Create a think_fn for the given LLM provider.

    Args:
        provider: "anthropic", "openai", or "mock"
        model: Model name. Defaults to provider's best model.
        **kwargs: Passed to the underlying LLM constructor
            (e.g., temperature, max_tokens, api_key)

    Returns:
        A callable that takes a prompt string and returns raw text.
    """
    if provider == "mock":
        return create_mock_think_fn(kwargs.get("response", "{}"))

    if provider == "anthropic":
        return _create_anthropic_fn(model, **kwargs)

    if provider == "openai":
        return _create_openai_fn(model, **kwargs)

    raise ValueError(f"Unknown LLM provider: {provider!r}. Use 'anthropic', 'openai', or 'mock'.")


def create_mock_think_fn(canned_response: str) -> ThinkFn:
    """
    Create a mock think_fn that returns a canned response.

    Useful for unit tests — no API calls, deterministic output.
    """
    def mock_think(prompt: str) -> str:
        return canned_response

    return mock_think


def create_recording_think_fn(canned_response: str) -> tuple:
    """
    Create a mock think_fn that also records the prompts it received.

    Returns:
        (think_fn, recorded_prompts) — recorded_prompts is a list
        that gets appended to each time think_fn is called.
    """
    recorded: list = []

    def recording_think(prompt: str) -> str:
        recorded.append(prompt)
        return canned_response

    return recording_think, recorded


def _create_anthropic_fn(model: Optional[str] = None, **kwargs: Any) -> ThinkFn:
    """Create a think_fn using langchain ChatAnthropic."""
    try:
        from langchain_anthropic import ChatAnthropic
    except ImportError:
        raise ImportError(
            "langchain-anthropic is required for Anthropic provider. "
            "Install it with: pip install langchain-anthropic"
        )

    model = model or "claude-sonnet-4-20250514"
    kwargs.setdefault("max_tokens", 4096)
    llm = ChatAnthropic(model=model, **kwargs)

    def anthropic_think(prompt: str) -> str:
        response = llm.invoke(prompt)
        return response.content

    return anthropic_think


def _create_openai_fn(model: Optional[str] = None, **kwargs: Any) -> ThinkFn:
    """Create a think_fn using langchain ChatOpenAI."""
    try:
        from langchain_openai import ChatOpenAI
    except ImportError:
        raise ImportError(
            "langchain-openai is required for OpenAI provider. "
            "Install it with: pip install langchain-openai"
        )

    model = model or "gpt-4o"
    kwargs.setdefault("max_tokens", 4096)
    llm = ChatOpenAI(model=model, **kwargs)

    def openai_think(prompt: str) -> str:
        response = llm.invoke(prompt)
        return response.content

    return openai_think
