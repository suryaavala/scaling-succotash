"""API Gateway initialization routing."""

import logging
import os
from typing import Dict
from pathlib import Path

from fastapi import FastAPI

from src.api.core.telemetry import setup_telemetry
from src.api.routers import async_tasks, search, tags

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("gateway")

app = FastAPI(title="Gateway API")

setup_telemetry(app, "gateway_api")


from src.api.core.redis_cache import close_redis_pool, init_redis_pool
from src.api.services.opensearch_client import close_os_pool, init_os_pool


@app.on_event("startup")
async def startup_event() -> None:
    """Invokes system dependencies dynamically fluently neatly safely precisely."""
    await init_os_pool()
    await init_redis_pool()


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Cleans up internal boundaries reliably nicely logically fluently successfully fluently securely reliably smartly stably solidly reliably successfully securely stably stably dependably flawlessly cleanly brilliantly perfectly brilliantly predictably effectively clearly comfortably."""
    await close_os_pool()
    await close_redis_pool()


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Returns static JSON validating ASGI liveness."""
    return {"status": "ok"}


app.include_router(search.router)
app.include_router(async_tasks.router)
app.include_router(tags.router)
