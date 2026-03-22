"""Search service for building OpenSearch DSL queries."""

import logging
from typing import Any, Dict, List

from src.api.models.schemas import SearchRequest

logger = logging.getLogger("search_service")


def build_search_dsl(request: SearchRequest) -> Dict[str, Any]:
    """Translate a SearchRequest into an OpenSearch DSL query."""
    must_clauses: List[Dict[str, Any]] = []
    filter_clauses: List[Dict[str, Any]] = []

    if request.name:
        must_clauses.append({"match": {"name": request.name}})

    if request.industry:
        filter_clauses.append({"term": {"industry.keyword": request.industry.lower()}})

    if request.size_range:
        filter_clauses.append({"term": {"size_range.keyword": request.size_range.lower()}})

    if request.country:
        filter_clauses.append({"term": {"country.keyword": request.country.lower()}})

    if request.tags:
        for tag in request.tags:
            filter_clauses.append({"term": {"tags": tag}})

    year_range: Dict[str, int] = {}
    if request.year_from:
        year_range["gte"] = request.year_from
    if request.year_to:
        year_range["lte"] = request.year_to

    if year_range:
        filter_clauses.append({"range": {"year_founded": year_range}})

    bool_query: Dict[str, Any] = {}
    if must_clauses:
        bool_query["must"] = must_clauses
    if filter_clauses:
        bool_query["filter"] = filter_clauses

    # If no criteria provided, match all
    query: Dict[str, Any]
    if not bool_query:
        query = {"match_all": {}}
    else:
        query = {"bool": bool_query}

    dsl = {
        "query": query,
        "from": (request.page - 1) * request.size,
        "size": request.size,
    }
    return dsl
