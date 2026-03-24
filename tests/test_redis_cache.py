"""Unit tests for Redis cache operations."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import redis.exceptions

from src.api.core import redis_cache


@pytest.fixture(autouse=True)
def reset_redis_client() -> Any:
    """Reset the redis client before/after each test."""
    original = redis_cache._redis_client
    yield
    redis_cache._redis_client = original


def test_get_hash_consistency() -> None:
    """Test that hashes are consistent for the same normalized input."""
    h1 = redis_cache.get_hash("Test Query")
    h2 = redis_cache.get_hash("  test query  ")
    assert h1 == h2


def test_get_hash_different_input() -> None:
    """Test that different inputs produce different hashes."""
    h1 = redis_cache.get_hash("query a")
    h2 = redis_cache.get_hash("query b")
    assert h1 != h2


@pytest.mark.asyncio
async def test_get_cached_intent_returns_none_when_no_client() -> None:
    """Test that cache returns None when no Redis client."""
    redis_cache._redis_client = None
    result = await redis_cache.get_cached_intent("test")
    assert result is None


@pytest.mark.asyncio
async def test_set_cached_intent_noop_when_no_client() -> None:
    """Test that set is a no-op when no Redis client."""
    redis_cache._redis_client = None
    await redis_cache.set_cached_intent("test", {"key": "val"})  # Should not raise


@pytest.mark.asyncio
async def test_get_cached_intent_returns_data() -> None:
    """Test that cached intent data is returned correctly."""
    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value='{"industry": "tech"}')
    redis_cache._redis_client = mock_client
    result = await redis_cache.get_cached_intent("test")
    assert result == {"industry": "tech"}


@pytest.mark.asyncio
async def test_get_cached_intent_returns_none_on_miss() -> None:
    """Test cache miss returns None."""
    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=None)
    redis_cache._redis_client = mock_client
    result = await redis_cache.get_cached_intent("test")
    assert result is None


@pytest.mark.asyncio
async def test_get_cached_intent_returns_none_on_error() -> None:
    """Test cache error returns None gracefully."""
    mock_client = MagicMock()
    mock_client.get = AsyncMock(side_effect=Exception("Redis error"))
    redis_cache._redis_client = mock_client
    result = await redis_cache.get_cached_intent("test")
    assert result is None


@pytest.mark.asyncio
async def test_get_cached_intent_handles_chaos_connection_error() -> None:
    """Test global connection failure drops silently."""
    mock_client = MagicMock()
    mock_client.get = AsyncMock(side_effect=redis.exceptions.ConnectionError("Connection refused"))
    redis_cache._redis_client = mock_client
    result = await redis_cache.get_cached_intent("test chaos error")
    assert result is None


@pytest.mark.asyncio
async def test_get_cached_intent_handles_chaos_timeout_error() -> None:
    """Test strict timeout drops silently bypassing blocks."""
    mock_client = MagicMock()
    mock_client.get = AsyncMock(side_effect=redis.exceptions.TimeoutError("Cache timeout"))
    redis_cache._redis_client = mock_client
    result = await redis_cache.get_cached_intent("test chaos timeout")
    assert result is None


@pytest.mark.asyncio
async def test_set_cached_intent_calls_setex() -> None:
    """Test that set stores data with TTL."""
    mock_client = MagicMock()
    mock_client.setex = AsyncMock()
    redis_cache._redis_client = mock_client
    await redis_cache.set_cached_intent("test", {"industry": "tech"})
    mock_client.setex.assert_called_once()


@pytest.mark.asyncio
async def test_set_cached_intent_handles_error() -> None:
    """Test that set handles errors gracefully."""
    mock_client = MagicMock()
    mock_client.setex = AsyncMock(side_effect=Exception("Redis write error"))
    redis_cache._redis_client = mock_client
    await redis_cache.set_cached_intent("test", {"key": "val"})  # Should not raise


@pytest.mark.asyncio
async def test_set_cached_intent_handles_chaos_connection_error() -> None:
    """Test set handles connection errors organically."""
    mock_client = MagicMock()
    mock_client.setex = AsyncMock(side_effect=redis.exceptions.ConnectionError("Connection refused"))
    redis_cache._redis_client = mock_client
    await redis_cache.set_cached_intent("test chaos write error", {"key": "val"})  # Should not raise


@pytest.mark.asyncio
async def test_get_cached_search_returns_none_when_no_client() -> None:
    """Test search cache returns None when no Redis client."""
    redis_cache._redis_client = None
    result = await redis_cache.get_cached_search("test")
    assert result is None


@pytest.mark.asyncio
async def test_get_cached_search_returns_data() -> None:
    """Test search cache returns data correctly."""
    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value='{"results": []}')
    redis_cache._redis_client = mock_client
    result = await redis_cache.get_cached_search("test")
    assert result == {"results": []}


@pytest.mark.asyncio
async def test_set_cached_search_noop_when_no_client() -> None:
    """Test search cache set is a no-op when no Redis client."""
    redis_cache._redis_client = None
    await redis_cache.set_cached_search("test", {"results": []})  # Should not raise


@pytest.mark.asyncio
async def test_set_cached_search_calls_setex() -> None:
    """Test that search cache stores data with TTL."""
    mock_client = MagicMock()
    mock_client.setex = AsyncMock()
    redis_cache._redis_client = mock_client
    await redis_cache.set_cached_search("test", {"results": []})
    mock_client.setex.assert_called_once()


@pytest.mark.asyncio
async def test_get_cached_search_handles_chaos_error() -> None:
    """Test get search handles connection failures dynamically."""
    mock_client = MagicMock()
    mock_client.get = AsyncMock(side_effect=redis.exceptions.ConnectionError("Connection refused"))
    redis_cache._redis_client = mock_client
    result = await redis_cache.get_cached_search("test chaos error")
    assert result is None


@pytest.mark.asyncio
async def test_set_cached_search_handles_chaos_error() -> None:
    """Test set search handles timeout interruptions silently."""
    mock_client = MagicMock()
    mock_client.setex = AsyncMock(side_effect=redis.exceptions.TimeoutError("Timeout"))
    redis_cache._redis_client = mock_client
    await redis_cache.set_cached_search("test chaos write error", {"results": []})  # Should not raise


@pytest.mark.asyncio
@patch("src.api.core.redis_cache.redis")
async def test_init_redis_pool(mock_redis: MagicMock) -> None:
    """Test Redis pool initialization."""
    mock_pool = MagicMock()
    mock_redis.ConnectionPool.from_url.return_value = mock_pool
    mock_redis.Redis.return_value = MagicMock()
    await redis_cache.init_redis_pool()
    assert redis_cache._redis_client is not None


@pytest.mark.asyncio
async def test_close_redis_pool() -> None:
    """Test Redis pool closure."""
    mock_client = MagicMock()
    mock_client.close = AsyncMock()
    redis_cache._redis_client = mock_client
    await redis_cache.close_redis_pool()
    assert redis_cache._redis_client is None
    mock_client.close.assert_called_once()


@pytest.mark.asyncio
async def test_close_redis_pool_noop_when_none() -> None:
    """Test close is a no-op when client is None."""
    redis_cache._redis_client = None
    await redis_cache.close_redis_pool()  # Should not raise
