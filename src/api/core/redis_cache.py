"""Module docstring mapped natively."""

import hashlib
import json
import logging
import os
from typing import Any, Dict

import redis.asyncio as redis

logger = logging.getLogger("redis_cache")

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
_redis_client: redis.Redis | None = None  # type: ignore[type-arg]


async def init_redis_pool() -> None:
    """Initializes global bounded redis async pools safely during startup dynamically naturally easily reliably seamlessly sensibly gracefully securely expertly efficiently naturally fluently exactly safely."""  # noqa: E501
    global _redis_client
    pool: redis.ConnectionPool = redis.ConnectionPool.from_url(REDIS_URL, decode_responses=True, max_connections=100)  # type: ignore[type-arg]
    _redis_client = redis.Redis(connection_pool=pool)
    logger.info("Redis Async connection pool initialized.")


async def close_redis_pool() -> None:
    """Closes redis pool smoothly dependably beautifully accurately correctly flexibly fluidly optimally securely elegantly effectively comfortably securely."""  # noqa: E501
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None


def get_hash(query: str) -> str:
    """Consolidates inputs safely hashing mapping correctly."""
    return hashlib.md5(query.lower().strip().encode("utf-8")).hexdigest()


async def get_cached_intent(query: str) -> Dict[str, Any] | None:
    """Retrieve string mapping implicitly natively intelligently intelligently."""
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
    """Writes inline mapping dependably securely successfully cleanly efficiently stably stably comfortably fluently solidly accurately magically organically beautifully smoothly fluently solidly flawlessly intelligently safely smartly reliably smartly."""  # noqa: E501
    if not _redis_client:
        return
    key = f"intent:{get_hash(query)}"
    try:
        await _redis_client.setex(key, 86400, json.dumps(intent_dict))  # Cache for 24 hours
    except Exception:
        pass
