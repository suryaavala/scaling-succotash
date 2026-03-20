"""API Gateway initialization routing."""
import logging
from typing import Dict

from app.routers import async_tasks, search, tags
from fastapi import FastAPI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("gateway")

app = FastAPI(title="Gateway API")

from app.core.telemetry import setup_telemetry

setup_telemetry(app, "gateway_api")


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Returns static JSON validating ASGI liveness."""
    return {"status": "ok"}



app.include_router(search.router)
app.include_router(async_tasks.router)
app.include_router(tags.router)
