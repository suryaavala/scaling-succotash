import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from opensearchpy.exceptions import NotFoundError
from app.services.opensearch_client import get_opensearch_client, INDEX_NAME

router = APIRouter(prefix="/api/v2", tags=["Tags V2"])
logger = logging.getLogger("api")

class TagRequest(BaseModel):
    tag: str

@router.post("/companies/{company_id}/tags")
async def add_tag(company_id: str, request: TagRequest):
    client = get_opensearch_client()
    tag = request.tag.strip()
    
    script = {
        "script": {
            "source": """
            if (ctx._source.tags == null) {
                ctx._source.tags = new ArrayList();
            }
            if (!ctx._source.tags.contains(params.tag)) {
                ctx._source.tags.add(params.tag);
            }
            """,
            "lang": "painless",
            "params": {
                "tag": tag
            }
        }
    }
    
    try:
        response = client.update(index=INDEX_NAME, id=company_id, body=script, refresh=True)
        return {"status": "success", "tag": tag, "company_id": company_id}
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Company not found")
    except Exception as e:
        logger.error(f"Failed to update tag: {e}")
        raise HTTPException(status_code=500, detail="Failed to add tag")

@router.get("/tags", response_model=List[str])
async def get_all_tags():
    client = get_opensearch_client()
    
    agg_query = {
        "size": 0,
        "aggs": {
            "unique_tags": {
                "terms": {
                    "field": "tags",
                    "size": 1000
                }
            }
        }
    }
    
    try:
        response = client.search(index=INDEX_NAME, body=agg_query)
        buckets = response.get("aggregations", {}).get("unique_tags", {}).get("buckets", [])
        tags = [bucket["key"] for bucket in buckets]
        return tags
    except Exception as e:
        logger.error(f"Failed to get tags: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch tags")
