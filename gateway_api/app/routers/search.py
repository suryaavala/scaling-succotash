import logging

from app.services.llm_router import extract_intent
from app.services.opensearch_client import two_stage_retrieval
from fastapi import APIRouter
from pydantic import BaseModel

from app.models.schemas import SearchRequest, SearchResponse
from app.services.search_service import execute_search

router = APIRouter(prefix="/api/v2/search", tags=["Search API V2"])
logger = logging.getLogger("search")


@router.post("", response_model=SearchResponse)
async def deterministic_search(request: SearchRequest):
    results = execute_search(request)
    return SearchResponse(results=results)


class IntelligentSearchRequest(BaseModel):
    query: str


class IntelligentSearchResponse(BaseModel):
    results: list[dict]
    agentic_task_id: str | None = None


@router.post("/intelligent", response_model=IntelligentSearchResponse)
async def intelligent_search(request: IntelligentSearchRequest):
    intent = extract_intent(request.query)

    candidates = two_stage_retrieval(request.query, intent)

    task_id = None
    if intent.get("requires_agent"):
        from app.routers.async_tasks import (
            AgenticSearchRequest,
            dispatch_agentic_search,
        )

        resp = await dispatch_agentic_search(
            AgenticSearchRequest(query=request.query, candidates=candidates)
        )
        task_id = resp["task_id"]

    return IntelligentSearchResponse(results=candidates, agentic_task_id=task_id)
