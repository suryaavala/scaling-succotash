"""Domain models natively mapping Pydantic schema validation bounds."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class SearchRequest(BaseModel):
    """Standard payload validating baseline determinism natively."""

    name: Optional[str] = None
    industry: Optional[str] = None
    size_range: Optional[str] = None
    country: Optional[str] = None
    year_from: Optional[int] = None
    year_to: Optional[int] = None
    tags: Optional[List[str]] = None
    page: int = 1
    size: int = 10


class SearchResponse(BaseModel):
    """Schema for legacy string filters."""

    results: List[Dict[str, Any]]


class IntelligentSearchRequest(BaseModel):
    """Schema for complex natural language semantic filtering."""

    query: str


class IntelligentSearchResponse(BaseModel):
    """Schema returning semantic candidates or task ids."""

    results: List[Dict[str, Any]]
    agentic_task_id: Optional[str] = None


class AgenticSearchRequest(BaseModel):
    """Schema dispatching Celery tasks for nested synthesis."""

    query: str
    candidates: List[Dict[str, Any]]


class TaskStatusResponse(BaseModel):
    """Schema returning Celery task bounds."""

    task_id: str
    status: str
    result: Optional[str] = None


class TagRequest(BaseModel):
    """Schema defining string payload tags."""

    tag: str
