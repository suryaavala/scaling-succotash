from pydantic import BaseModel
from typing import Optional, List

class SearchRequest(BaseModel):
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
    results: list[dict]
