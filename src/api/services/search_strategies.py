"""Strategy Pattern implementations for search execution."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List

from src.api.models.schemas import (
    AgenticSearchRequest,
    IntelligentSearchResponse,
    SearchRequest,
    SearchResponse,
)
from src.api.routers.async_tasks import dispatch_agentic_search
from src.api.services.search_service import build_search_dsl


class SearchStrategy(ABC):
    """Abstract base strategy for all search execution modes."""

    @abstractmethod
    async def execute(self, query: str, candidates: List[Dict[str, Any]]) -> IntelligentSearchResponse:
        """Execute the search strategy against the given candidates."""
        ...


class DeterministicSearchStrategy:
    """Strategy for structured filter-based search via OpenSearch DSL."""

    async def execute(self, request: SearchRequest, repository: Any) -> SearchResponse:
        """Build DSL from request and execute against the repository."""
        dsl = build_search_dsl(request)
        results = await repository.search(dsl)
        return SearchResponse(results=results)


class SemanticSearchStrategy(SearchStrategy):
    """Concrete strategy returning synchronous candidate arrays."""

    async def execute(self, query: str, candidates: List[Dict[str, Any]]) -> IntelligentSearchResponse:
        """Return candidates directly without agentic processing."""
        return IntelligentSearchResponse(results=candidates, agentic_task_id=None)


class AgenticSearchStrategy(SearchStrategy):
    """Concrete strategy delegating to Celery for async synthesis."""

    async def execute(self, query: str, candidates: List[Dict[str, Any]]) -> IntelligentSearchResponse:
        """Dispatch candidates to Celery worker and return task ID."""
        resp = await dispatch_agentic_search(AgenticSearchRequest(query=query, candidates=candidates))
        task_id = resp["task_id"]
        return IntelligentSearchResponse(results=candidates, agentic_task_id=task_id)


class SearchContext:
    """Strategy context that delegates to the configured search strategy."""

    def __init__(self, strategy: SearchStrategy) -> None:
        """Initialize with a concrete strategy."""
        self._strategy = strategy

    async def execute_search(self, query: str, candidates: List[Dict[str, Any]]) -> IntelligentSearchResponse:
        """Execute the strategy's search logic."""
        return await self._strategy.execute(query, candidates)
