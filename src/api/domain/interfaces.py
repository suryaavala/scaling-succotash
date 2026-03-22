"""Abstract domain interfaces enforcing Repository and Strategy patterns."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class CompanyRepository(ABC):
    """Abstract repository for company data access operations."""

    @abstractmethod
    async def search(self, query_dsl: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute a raw DSL search and return source documents with IDs."""
        ...

    @abstractmethod
    async def two_stage_retrieval(
        self, query: str, intent: Dict[str, Any], vector: list[float]
    ) -> List[Dict[str, Any]]:
        """Hybrid kNN + text retrieval with reranking."""
        ...

    @abstractmethod
    async def add_tag(self, company_id: str, tag: str) -> Dict[str, str]:
        """Add a tag to a company document."""
        ...

    @abstractmethod
    async def get_all_tags(self) -> List[str]:
        """Retrieve all unique tags across the index."""
        ...
