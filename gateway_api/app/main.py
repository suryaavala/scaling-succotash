import logging
from fastapi import FastAPI
from app.routers import search, async_tasks, tags

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("gateway")

app = FastAPI(title="Gateway API")

from app.core.telemetry import setup_telemetry
setup_telemetry(app, "gateway_api")

@app.get("/health")
async def health_check():
    return {"status": "ok"}

app.include_router(search.router)
app.include_router(async_tasks.router)
app.include_router(tags.router)
