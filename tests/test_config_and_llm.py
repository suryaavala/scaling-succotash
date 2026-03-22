"""Unit tests for centralized config and LLM router edge cases."""

from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from src.api.core.config import Settings, get_settings
from src.api.services.llm_router import LLMClient


def test_settings_defaults() -> None:
    """Test Settings loads with sensible defaults."""
    settings = Settings()
    assert settings.opensearch_url == "http://localhost:9200"
    assert settings.redis_url == "redis://localhost:6379/0"
    assert settings.opensearch_index == "companies"
    assert settings.redis_cache_ttl == 86400


def test_get_settings_returns_instance() -> None:
    """Test get_settings returns a Settings object."""
    get_settings.cache_clear()
    settings = get_settings()
    assert isinstance(settings, Settings)


# --- LLM Router edge case tests ---


@pytest.mark.asyncio
async def test_extract_intent_fast_path_kubernetes() -> None:
    """Test fast-path heuristic for kubernetes query."""
    client = LLMClient()
    intent, is_cached = await client.extract_intent("cloud providers supporting kubernetes")
    assert intent["industry"] == "Software"
    assert intent["requires_agent"] is False
    assert is_cached is True


@pytest.mark.asyncio
async def test_extract_intent_fast_path_agentic() -> None:
    """Test fast-path heuristic for agentic query."""
    client = LLMClient()
    intent, is_cached = await client.extract_intent("latest acquisitions by Microsoft in AI")
    assert intent["requires_agent"] is True
    assert is_cached is True


@pytest.mark.asyncio
async def test_extract_intent_fallback_on_error() -> None:
    """Test that LLM errors fall back to default intent."""
    client = LLMClient()
    with (
        patch(
            "src.api.services.llm_router.get_cached_intent",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch(
            "src.api.services.llm_router.acompletion",
            new_callable=AsyncMock,
            side_effect=Exception("API down"),
        ),
    ):
        intent, is_cached = await client.extract_intent("something random")
    assert intent["requires_agent"] is False
    assert is_cached is False


@pytest.mark.asyncio
async def test_extract_intent_mock_llm_latency() -> None:
    """Test mock LLM latency mode returns deterministic results."""
    client = LLMClient()
    with (
        patch.dict("os.environ", {"MOCK_LLM_LATENCY": "0.01"}),
        patch(
            "src.api.services.llm_router.get_cached_intent",
            new_callable=AsyncMock,
            return_value=None,
        ),
    ):
        get_settings.cache_clear()
        intent, is_cached = await client.extract_intent("who founded acme")
    assert intent["requires_agent"] is True  # "who" triggers agent
    assert is_cached is False
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_extract_intent_cached_result() -> None:
    """Test intent retrieved from Redis cache."""
    client = LLMClient()
    cached_intent: dict[str, Any] = {"industry": "Healthcare", "requires_agent": False}
    with patch(
        "src.api.services.llm_router.get_cached_intent",
        new_callable=AsyncMock,
        return_value=cached_intent,
    ):
        intent, is_cached = await client.extract_intent("healthcare companies")
    assert intent["industry"] == "Healthcare"
    assert is_cached is True
