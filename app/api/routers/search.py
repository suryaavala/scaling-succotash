import logging
from fastapi import APIRouter, HTTPException, Depends
from opensearchpy.exceptions import ConnectionError, TransportError

from app.models.schemas import SearchRequest, SearchResponse, Company
from app.services.search_service import build_search_dsl
from app.core.opensearch_client import get_opensearch_client, INDEX_NAME

router = APIRouter(prefix="/api/v1/search", tags=["Search"])
logger = logging.getLogger("api")

@router.post("", response_model=SearchResponse)
async def standard_search(request: SearchRequest):
    dsl = build_search_dsl(request)
    client = get_opensearch_client()
    
    try:
        response = client.search(index=INDEX_NAME, body=dsl)
        
        hits = response["hits"]["hits"]
        total = response["hits"]["total"]["value"]
        
        results = []
        for hit in hits:
            source = hit["_source"]
            company = Company(
                id=hit["_id"],
                name=source.get("name", ""),
                domain=source.get("domain"),
                industry=source.get("industry"),
                locality=source.get("locality"),
                country=source.get("country"),
                size_range=source.get("size_range"),
                year_founded=source.get("year_founded"),
                tags=source.get("tags", [])
            )
            results.append(company)
            
        return SearchResponse(
            total=total,
            page=request.page,
            size=request.size,
            results=results
        )
        
    except ConnectionError as e:
        logger.error(f"OpenSearch Connection Error: {str(e)}")
        raise HTTPException(status_code=503, detail="Search service unavailable")
    except TransportError as e:
        raise HTTPException(status_code=500, detail="Search query failed")

from pydantic import BaseModel
from app.services.intelligence_service import extract_intent, hybrid_search
from app.services.agent_service import synthesize_agent_response

class IntelligentSearchRequest(BaseModel):
    query: str

class IntelligentSearchResponse(BaseModel):
    agentic_answer: str | None = None
    search_results: SearchResponse | None = None

@router.post("/intelligent", response_model=IntelligentSearchResponse)
async def intelligent_search(request: IntelligentSearchRequest):
    intent = extract_intent(request.query)
    
    search_response = hybrid_search(request.query, intent)
    
    if intent.requires_agent:
        answer = synthesize_agent_response(request.query, search_response.results)
        return IntelligentSearchResponse(
            agentic_answer=answer,
            search_results=search_response
        )
    else:
        return IntelligentSearchResponse(
            search_results=search_response
        )
