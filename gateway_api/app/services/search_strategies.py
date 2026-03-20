"""Strategy Pattern interface mapping intelligent search executions."""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from app.models.schemas import IntelligentSearchResponse, AgenticSearchRequest
from app.routers.async_tasks import dispatch_agentic_search


class IntelligentSearchStrategy(ABC):
    """Base Strategy for resolving semantic search candidates."""
    
    @abstractmethod
    async def execute(self, query: str, candidates: List[Dict[str, Any]]) -> IntelligentSearchResponse:
        pass


class SemanticSearchStrategy(IntelligentSearchStrategy):
    """Concrete strategy returning synchronous candidate arrays natively."""
    
    async def execute(self, query: str, candidates: List[Dict[str, Any]]) -> IntelligentSearchResponse:
        return IntelligentSearchResponse(results=candidates, agentic_task_id=None)


class AgenticSearchStrategy(IntelligentSearchStrategy):
    """Concrete strategy delegating async RabbitMQ synthesis flows."""
    
    async def execute(self, query: str, candidates: List[Dict[str, Any]]) -> IntelligentSearchResponse:
        resp = await dispatch_agentic_search(
            AgenticSearchRequest(query=query, candidates=candidates)
        )
        task_id = resp["task_id"]
        return IntelligentSearchResponse(results=candidates, agentic_task_id=task_id)


class SearchContext:
    """Strategy context explicitly executing bound search resolution modes."""
    
    def __init__(self, strategy: IntelligentSearchStrategy):
        self._strategy = strategy
        
    async def execute_search(self, query: str, candidates: List[Dict[str, Any]]) -> IntelligentSearchResponse:
        return await self._strategy.execute(query, candidates)
