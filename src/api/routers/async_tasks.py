"""Async task management endpoints for Celery-backed agentic workflows."""

import logging
from typing import Any, Dict

from celery.result import AsyncResult
from fastapi import APIRouter

from src.api.core.config import get_settings
from src.api.models.schemas import AgenticSearchRequest, TaskStatusResponse
from src.worker.agent_workflows import celery_app

router = APIRouter(prefix="/api/v2", tags=["Async Tasks"])
logger = logging.getLogger("async_tasks")


@router.post("", response_model=Dict[str, Any])
async def dispatch_agentic_search(request: AgenticSearchRequest) -> Dict[str, Any]:
    """Dispatch a heavy query to the Celery worker for agentic synthesis."""
    _ = get_settings()  # Validate config is available
    task = celery_app.send_task(
        "tasks.agent_workflows.synthesize_agent_response",
        args=[request.query, request.candidates],
    )
    return {"task_id": task.id, "status": "processing"}


@router.get("/search/agentic/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str) -> TaskStatusResponse:
    """Retrieve the status and result of a Celery task."""
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
