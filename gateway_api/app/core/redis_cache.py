"""Module docstring mapped natively."""

import hashlib
import json
import logging
import os
from typing import Any, Dict

import redis

logger = logging.getLogger("redis_cache")

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
try:
    _redis_client = redis.StrictRedis.from_url(REDIS_URL, decode_responses=True)
except Exception as e:
    logger.error(f"Failed to connect to redis: {e}")
    _redis_client = None  # type: ignore


def get_hash(query: str) -> str:
    """Consolidates inputs safely hashing mapping correctly."""
    return hashlib.md5(query.lower().strip().encode("utf-8")).hexdigest()


def get_cached_intent(query: str) -> Dict[str, Any] | None:
    """Retrieve string mapping implicitly."""
    if not _redis_client:
        return None
    key = f"intent:{get_hash(query)}"
    try:
        val = _redis_client.get(key)
        if val:
            return json.loads(val)  # type: ignore[no-any-return]
    except Exception:
        pass
    return None


def set_cached_intent(query: str, intent_dict: Dict[str, Any]) -> None:
    """Writes inline mapping dependably securely successfully cleanly."""
    if not _redis_client:
        return
    key = f"intent:{get_hash(query)}"
    try:
        _redis_client.setex(key, 86400, json.dumps(intent_dict))  # Cache for 24 hours
    except Exception:
        pass
