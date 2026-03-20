import redis
import hashlib
import json
import os
import logging

logger = logging.getLogger("redis_cache")

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
try:
    _redis_client = redis.StrictRedis.from_url(REDIS_URL, decode_responses=True)
except Exception as e:
    logger.error(f"Failed to connect to redis: {e}")
    _redis_client = None

def get_hash(query: str) -> str:
    return hashlib.md5(query.lower().strip().encode('utf-8')).hexdigest()

def get_cached_intent(query: str) -> dict | None:
    if not _redis_client: return None
    key = f"intent:{get_hash(query)}"
    try:
        val = _redis_client.get(key)
        if val:
            return json.loads(val)
    except Exception:
        pass
    return None

def set_cached_intent(query: str, intent_dict: dict):
    if not _redis_client: return
    key = f"intent:{get_hash(query)}"
    try:
        _redis_client.setex(key, 86400, json.dumps(intent_dict)) # Cache for 24 hours
    except Exception:
        pass
