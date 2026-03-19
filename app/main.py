import time
import logging
from fastapi import FastAPI, Request

# Configure structured JSON logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api")

app = FastAPI(
    title="Enterprise B2B Company Search & Intelligence API",
    version="1.0.0"
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000  # ms
    
    log_dict = {
        "method": request.method,
        "path": request.url.path,
        "status_code": response.status_code,
        "latency_ms": round(process_time, 2)
    }
    logger.info(str(log_dict))
    
    return response

@app.get("/health")
async def health_check():
    return {"status": "ok"}

from app.api.routers import search, tags
app.include_router(search.router)
app.include_router(tags.router)
