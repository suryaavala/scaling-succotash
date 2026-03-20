import logging

from app.routers import search
from fastapi import FastAPI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("gateway")

app = FastAPI(title="Gateway API")

from app.core.telemetry import setup_telemetry

setup_telemetry(app, "gateway_api")


@app.get("/health")
async def health_check():
    return {"status": "ok"}


from app.routers import async_tasks, tags

app.include_router(search.router)
app.include_router(async_tasks.router)
app.include_router(tags.router)
