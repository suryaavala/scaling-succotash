"""Search routing logic for deterministic and intelligent search endpoints."""

import asyncio
import logging
from typing import Dict

from fastapi import APIRouter, Depends, Response

from src.api.core.redis_cache import get_cached_search, set_cached_search
from src.api.domain.interfaces import CompanyRepository
from src.api.models.schemas import (
    IntelligentSearchRequest,
    IntelligentSearchResponse,
    SearchRequest,
    SearchResponse,
)
from src.api.services.llm_router import LLMClient, get_llm_client
from src.api.services.opensearch_client import get_company_repository, get_embedding
from src.api.services.search_strategies import (
    AgenticSearchStrategy,
    DeterministicSearchStrategy,
    SearchContext,
    SearchStrategy,
    SemanticSearchStrategy,
)

router = APIRouter(prefix="/api/v2/search", tags=["Search API V2"])
logger = logging.getLogger("search")


@router.post("", response_model=SearchResponse)
async def deterministic_search(
    request: SearchRequest,
    repo: CompanyRepository = Depends(get_company_repository),
) -> SearchResponse:
    """Execute a structured filter-based search."""
    strategy = DeterministicSearchStrategy()
    response_payload = await strategy.execute(request, repo)
    response_payload.diagnostics = {
        "route": "Deterministic",
        "intent": {},
        "scores": [],
    }
    return response_payload


_flight_cache: Dict[str, asyncio.Event] = {}


@router.post("/intelligent", response_model=IntelligentSearchResponse)
async def intelligent_search(
    request: IntelligentSearchRequest,
    response: Response,
    repo: CompanyRepository = Depends(get_company_repository),
    llm_client: LLMClient = Depends(get_llm_client),
) -> IntelligentSearchResponse:
    """Route intelligent queries via LLM intent extraction and Strategy selection."""
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

        candidates = await repo.two_stage_retrieval(query, intent, vector)

        strategy_name = "AgenticSearch" if intent.get("requires_agent") else "SemanticSearch"
        strategy: SearchStrategy
        if intent.get("requires_agent"):
            strategy = AgenticSearchStrategy()
        else:
            strategy = SemanticSearchStrategy()

        context = SearchContext(strategy)
        result = await context.execute_search(query, candidates)

        # Build diagnostics
        diagnostics = {
            "route": strategy_name,
            "intent": intent,
            "scores": [
                {
                    "company_id": c.get("id"),
                    "name": c.get("name"),
                    "re_rank_score": c.get("re_rank_score"),
                    "knn_score": c.get("knn_score"),
                }
                for c in candidates
            ],
        }
        result.diagnostics = diagnostics

        await set_cached_search(query, result.model_dump())
        return result
    finally:
        event.set()
        _flight_cache.pop(query, None)
