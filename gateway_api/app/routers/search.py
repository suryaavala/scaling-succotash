"""Search routing logic natively mapping deterministic layouts."""
import logging

from app.models.schemas import (
    SearchRequest, SearchResponse, IntelligentSearchRequest, IntelligentSearchResponse
)
from app.services.llm_router import LLMClient, get_llm_client
from app.services.opensearch_client import OSClient, get_os_client
from app.services.search_service import execute_search
from app.services.search_strategies import SearchContext, AgenticSearchStrategy, SemanticSearchStrategy
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/api/v2/search", tags=["Search API V2"])
logger = logging.getLogger("search")

@router.post("", response_model=SearchResponse)
async def deterministic_search(
    request: SearchRequest,
    os_client: OSClient = Depends(get_os_client)
) -> SearchResponse:
    """Routes deterministic schema executions resolving direct query bindings securely."""
    results = execute_search(request, os_client)
    return SearchResponse(results=results)


@router.post("/intelligent", response_model=IntelligentSearchResponse)
async def intelligent_search(
    request: IntelligentSearchRequest,
    os_client: OSClient = Depends(get_os_client),
    llm_client: LLMClient = Depends(get_llm_client)
) -> IntelligentSearchResponse:
    """Routes an intelligent string securely enforcing native Strategy interfaces natively."""
    intent = llm_client.extract_intent(request.query)
    candidates = os_client.two_stage_retrieval(request.query, intent)

    if intent.get("requires_agent"):
        strategy = AgenticSearchStrategy()
    else:
        strategy = SemanticSearchStrategy()
        
    context = SearchContext(strategy)
    return await context.execute_search(request.query, candidates)
