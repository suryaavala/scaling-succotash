import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.llm_router import extract_intent
from app.services.opensearch_client import two_stage_retrieval

router = APIRouter(prefix="/api/v2/search", tags=["Search API V2"])
logger = logging.getLogger("search")

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
        from app.routers.async_tasks import dispatch_agentic_search, AgenticSearchRequest
        resp = await dispatch_agentic_search(AgenticSearchRequest(query=request.query, candidates=candidates))
        task_id = resp["task_id"]
        
    return IntelligentSearchResponse(
        results=candidates,
        agentic_task_id=task_id
    )
