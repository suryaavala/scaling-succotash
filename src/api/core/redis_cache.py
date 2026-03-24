"""Redis cache module using centralized settings."""

import hashlib
import json
import logging
from typing import Any, Dict

import redis.asyncio as redis

from src.api.core.config import get_settings

logger = logging.getLogger("redis_cache")

_redis_client: redis.Redis | None = None  # type: ignore[type-arg]


async def init_redis_pool() -> None:
    """Initialize global bounded redis async connection pool."""
    global _redis_client
    settings = get_settings()
    pool: redis.ConnectionPool = redis.ConnectionPool.from_url(  # type: ignore[type-arg]
        settings.redis_url,
        decode_responses=True,
        max_connections=settings.redis_max_connections,
        socket_timeout=1.0,
        socket_connect_timeout=1.0,
    )
    _redis_client = redis.Redis(connection_pool=pool)
    logger.info("Redis async connection pool initialized.")


async def close_redis_pool() -> None:
    """Close redis pool gracefully."""
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None


def get_hash(query: str) -> str:
    """Generate an MD5 hash for cache key deduplication."""
    return hashlib.md5(query.lower().strip().encode("utf-8")).hexdigest()


async def get_cached_intent(query: str) -> Dict[str, Any] | None:
    """Retrieve cached LLM intent extraction result."""
    if not _redis_client:
        return None
    key = f"intent:{get_hash(query)}"
    try:
        val = await _redis_client.get(key)
        if val:
            return json.loads(val)  # type: ignore[no-any-return]
    except Exception:
        pass
    return None


async def set_cached_intent(query: str, intent_dict: Dict[str, Any]) -> None:
    """Cache an LLM intent extraction result."""
    if not _redis_client:
        return
    settings = get_settings()
    key = f"intent:{get_hash(query)}"
    try:
        await _redis_client.setex(key, settings.redis_cache_ttl, json.dumps(intent_dict))
    except Exception:
        pass


async def get_cached_search(query: str) -> Dict[str, Any] | None:
    """Retrieve cached full search results."""
    if not _redis_client:
        return None
    key = f"search:{get_hash(query)}"
    try:
        val = await _redis_client.get(key)
        if val:
            return json.loads(val)  # type: ignore[no-any-return]
    except Exception:
        pass
    return None


async def set_cached_search(query: str, results_dict: Dict[str, Any]) -> None:
    """Cache full search results."""
    if not _redis_client:
        return
    settings = get_settings()
    key = f"search:{get_hash(query)}"
    try:
        await _redis_client.setex(key, settings.redis_cache_ttl, json.dumps(results_dict))
    except Exception:
        pass
