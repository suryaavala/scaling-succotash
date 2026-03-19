from typing import Dict, Any
from app.models.schemas import SearchRequest
from app.core.opensearch_client import INDEX_NAME

def build_search_dsl(request: SearchRequest) -> Dict[str, Any]:
    """Translates the standard SearchRequest into OpenSearch Boolean DSL."""
    
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
        
    # Handle year ranges
    year_range = {}
    if request.year_from:
        year_range["gte"] = request.year_from
    if request.year_to:
        year_range["lte"] = request.year_to
        
    if year_range:
        filter_clauses.append({"range": {"year_founded": year_range}})
        
    # Assemble the boolean query
    bool_query = {}
    if must_clauses:
        bool_query["must"] = must_clauses
    if filter_clauses:
        bool_query["filter"] = filter_clauses
        
    # If no criteria provided, match all
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
