import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from opensearchpy.exceptions import ConnectionError, TransportError
from app.services.llm_router import extract_intent
from app.services.opensearch_client import two_stage_retrieval, get_opensearch_client, INDEX_NAME
from app.services.search_service import build_search_dsl
from app.models.schemas import SearchRequest, SearchResponse, Company

router = APIRouter(prefix="/api/v2/search", tags=["Search API V2"])
logger = logging.getLogger("search")

class IntelligentSearchRequest(BaseModel):
    query: str

class IntelligentSearchResponse(BaseModel):
    results: list[dict]
    agentic_task_id: str | None = None

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
        logger.error(f"Transport Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Search query failed")

@router.post("/intelligent", response_model=IntelligentSearchResponse)
async def intelligent_search(request: IntelligentSearchRequest):
    intent = extract_intent(request.query)
    
    candidates = two_stage_retrieval(request.query, intent)
    
    task_id = None
    if intent.get("requires_agent"):
        from app.routers.async_tasks import dispatch_agentic_search, AgenticSearchRequest
        resp = await dispatch_agentic_search(AgenticSearchRequest(query=request.query, candidates=candidates))
        task_id = resp["task_id"]
        
    return IntelligentSearchResponse(
        results=candidates,
        agentic_task_id=task_id
    )
