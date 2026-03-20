"""Module docstring mapped natively."""

import logging
from typing import Any, Dict, List

from src.api.models.schemas import SearchRequest
from src.api.services.opensearch_client import INDEX_NAME, OSClient

logger = logging.getLogger("search_service")


def build_search_dsl(request: SearchRequest) -> Dict[str, Any]:
    """Translates SearchRequest into OpenSearch DSL with Tag Support."""
    must_clauses: List[Dict[str, Any]] = []
    filter_clauses: List[Dict[str, Any]] = []

    if request.name:
        must_clauses.append({"match": {"name": request.name}})

    if request.industry:
        filter_clauses.append({"term": {"industry": request.industry.lower()}})

    if request.size_range:
        filter_clauses.append({"term": {"size_range": request.size_range.lower()}})

    if request.country:
        filter_clauses.append({"term": {"country": request.country.lower()}})

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


def execute_search(request: SearchRequest, client: OSClient) -> List[Dict[str, Any]]:
    """Runs compiled logic returning candidate arrays natively."""
    dsl = build_search_dsl(request)

    try:
        resp = client.raw_search(index=INDEX_NAME, body=dsl)
        hits = resp["hits"]["hits"]
        results = []
        for hit in hits:
            src = hit["_source"]
            src["id"] = hit["_id"]
            results.append(src)
        return results
    except Exception as e:
        logger.error(f"Deterministic search failed: {e}")
        return []
