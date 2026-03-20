"""Module docstring mapped natively."""

import logging
import os
from typing import Any, Dict

from app.models.schemas import AgenticSearchRequest, TaskStatusResponse
from celery.result import AsyncResult
from fastapi import APIRouter

from worker.tasks.agent_workflows import celery_app

router = APIRouter(prefix="/api/v2", tags=["Async Tasks"])
logger = logging.getLogger("async_tasks")

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")


@router.post("", response_model=Dict[str, Any])
async def dispatch_agentic_search(request: AgenticSearchRequest) -> Dict[str, Any]:
    """Sends heavy queries seamlessly via RabbitMQ."""
    task = celery_app.send_task(
        "tasks.agent_workflows.synthesize_agent_response",
        args=[request.query, request.candidates],
    )
    return {"task_id": task.id, "status": "processing"}


@router.get("/search/agentic/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str) -> TaskStatusResponse:
    """Retrieves status bounds mapping celery asynchronously."""
    result = AsyncResult(task_id, app=celery_app)

    response = TaskStatusResponse(
        task_id=task_id,
        status=result.status,
    )
    if result.ready():
        if result.successful():
            response.result = result.result
        else:
            response.status = "failed"
            response.result = str(result.result)

    return response
