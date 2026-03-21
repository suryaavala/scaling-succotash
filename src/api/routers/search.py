"""Search routing logic natively mapping deterministic layouts."""

import asyncio
import logging
from typing import Dict

from fastapi import APIRouter, Depends, Response

from src.api.models.schemas import (
    IntelligentSearchRequest,
    IntelligentSearchResponse,
    SearchRequest,
    SearchResponse,
)
from src.api.core.redis_cache import get_cached_search, set_cached_search
from src.api.services.llm_router import LLMClient, get_llm_client
from src.api.services.opensearch_client import OSClient, get_embedding, get_os_client
from src.api.services.search_service import execute_search
from src.api.services.search_strategies import (
    AgenticSearchStrategy,
    IntelligentSearchStrategy,
    SearchContext,
    SemanticSearchStrategy,
)

router = APIRouter(prefix="/api/v2/search", tags=["Search API V2"])
logger = logging.getLogger("search")


@router.post("", response_model=SearchResponse)
async def deterministic_search(request: SearchRequest, os_client: OSClient = Depends(get_os_client)) -> SearchResponse:
    """Routes deterministic schema directly."""
    results = await execute_search(request, os_client)
    return SearchResponse(results=results)


_flight_cache: Dict[str, asyncio.Event] = {}

@router.post("/intelligent", response_model=IntelligentSearchResponse)
async def intelligent_search(
    request: IntelligentSearchRequest,
    response: Response,
    os_client: OSClient = Depends(get_os_client),
    llm_client: LLMClient = Depends(get_llm_client),
) -> IntelligentSearchResponse:
    """Routes intelligent queries via defined Strategies."""
    query = request.query
    if query in _flight_cache:
        await _flight_cache[query].wait()
        
    cached_search = await get_cached_search(query)
    if cached_search is not None:
        response.headers["X-Cache-Hit"] = "true"
        return IntelligentSearchResponse(**cached_search)

    event = asyncio.Event()
    _flight_cache[query] = event

    try:
        intent_result, vector = await asyncio.gather(llm_client.extract_intent(query), get_embedding(query))
        intent, is_cached = intent_result

        if is_cached:
            response.headers["X-Cache-Hit"] = "true"

        candidates = await os_client.two_stage_retrieval(query, intent, vector)

        strategy: IntelligentSearchStrategy
        if intent.get("requires_agent"):
            strategy = AgenticSearchStrategy()
        else:
            strategy = SemanticSearchStrategy()

        context = SearchContext(strategy)
        result = await context.execute_search(query, candidates)

        await set_cached_search(query, result.model_dump())
        return result
    finally:
        event.set()
        _flight_cache.pop(query, None)
