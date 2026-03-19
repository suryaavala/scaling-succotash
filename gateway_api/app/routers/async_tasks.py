import logging
import os
from fastapi import APIRouter
from pydantic import BaseModel
from celery.result import AsyncResult
from celery import Celery

router = APIRouter(prefix="/api/v2", tags=["Async Tasks"])
logger = logging.getLogger("async_tasks")

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
celery_app = Celery("agent_workflows", broker=REDIS_URL, backend=REDIS_URL)

class AgenticSearchRequest(BaseModel):
    query: str
    candidates: list[dict]

class TaskResponse(BaseModel):
    task_id: str
    status: str
    result: str | None = None

@router.post("/search/agentic", status_code=202)
async def dispatch_agentic_search(request: AgenticSearchRequest):
    task = celery_app.send_task(
        "tasks.agent_workflows.synthesize_agent_response",
        args=[request.query, request.candidates]
    )
    return {"task_id": str(task.id)}

@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task_status(task_id: str):
    task_result = AsyncResult(task_id, app=celery_app)
    result = None
    if task_result.ready():
        result = task_result.result if task_result.successful() else "Task failed"
        
    return TaskResponse(
        task_id=task_id,
        status=task_result.status,
        result=result
    )
