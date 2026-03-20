import logging
from typing import Dict, Any
from app.models.schemas import SearchRequest
from app.services.opensearch_client import get_opensearch_client, INDEX_NAME

logger = logging.getLogger("search_service")

def build_search_dsl(request: SearchRequest) -> Dict[str, Any]:
    """Translates the standard SearchRequest into OpenSearch Boolean DSL with Tag Support."""
    must_clauses = []
    filter_clauses = []
    
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
            
    year_range = {}
    if request.year_from:
        year_range["gte"] = request.year_from
    if request.year_to:
        year_range["lte"] = request.year_to
        
    if year_range:
        filter_clauses.append({"range": {"year_founded": year_range}})
        
    bool_query = {}
    if must_clauses:
        bool_query["must"] = must_clauses
    if filter_clauses:
        bool_query["filter"] = filter_clauses
        
    if not bool_query:
        query = {"match_all": {}}
    else:
        query = {"bool": bool_query}
        
    dsl = {
        "query": query,
        "from": (request.page - 1) * request.size,
        "size": request.size
    }
    return dsl

def execute_search(request: SearchRequest) -> list[dict]:
    client = get_opensearch_client()
    dsl = build_search_dsl(request)
    
    try:
        resp = client.search(index=INDEX_NAME, body=dsl)
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
