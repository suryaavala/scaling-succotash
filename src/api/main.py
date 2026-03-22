"""API Gateway initialization with lifespan management."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Dict

from fastapi import FastAPI

from src.api.core.redis_cache import close_redis_pool, init_redis_pool
from src.api.core.telemetry import setup_telemetry
from src.api.routers import async_tasks, search, tags
from src.api.services.opensearch_client import close_os_pool, init_os_pool

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("gateway")


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    """Manage startup and shutdown lifecycle events."""
    await init_os_pool()
    await init_redis_pool()
    logger.info("Gateway API started.")
    yield
    await close_os_pool()
    await close_redis_pool()
    logger.info("Gateway API shut down.")


app = FastAPI(title="Gateway API", lifespan=lifespan)

setup_telemetry(app, "gateway_api")


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Return static JSON validating ASGI liveness."""
    return {"status": "ok"}


app.include_router(search.router)
app.include_router(async_tasks.router)
app.include_router(tags.router)
