from typing import List, Optional
from pydantic import BaseModel, HttpUrl

class Company(BaseModel):
    id: str
    name: str
    domain: Optional[str] = None
    industry: Optional[str] = None
    locality: Optional[str] = None
    country: Optional[str] = None
    size_range: Optional[str] = None
    year_founded: Optional[int] = None
    tags: List[str] = []

class SearchRequest(BaseModel):
    name: Optional[str] = None
    industry: Optional[str] = None
    size_range: Optional[str] = None
    country: Optional[str] = None
    year_from: Optional[int] = None
    year_to: Optional[int] = None
    page: int = 1
    size: int = 20

class SearchResponse(BaseModel):
    total: int
    page: int
    size: int
    results: List[Company]
