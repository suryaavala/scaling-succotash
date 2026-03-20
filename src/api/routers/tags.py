"""Module docstring mapped natively."""

import logging
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException
from opensearchpy.exceptions import NotFoundError

from src.api.models.schemas import TagRequest
from src.api.services.opensearch_client import INDEX_NAME, OSClient, get_os_client

router = APIRouter(prefix="/api/v2", tags=["Tags"])
logger = logging.getLogger("api")


@router.post("/companies/{company_id}/tags")
async def add_tag(
    company_id: str, request: TagRequest, os_client: OSClient = Depends(get_os_client)
) -> Dict[str, str]:
    """Adds a dynamic tag mapped strictly against OpenSearch bounds."""
    client = os_client.client
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
            "params": {"tag": tag},
        }
    }

    try:
        client.update(index=INDEX_NAME, id=company_id, body=script, refresh=True)
        return {"status": "success", "tag": tag, "company_id": company_id}
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Company not found")
    except Exception as e:
        logger.error(f"Failed to update tag: {e}")
        raise HTTPException(status_code=500, detail="Failed to add tag")


@router.get("/tags")
async def get_all_tags(
    os_client: OSClient = Depends(get_os_client),
) -> list[str]:
    """Fetches mapped unique tags solidly natively from indices."""
    client = os_client.client

    agg_query = {
        "size": 0,
        "aggs": {"unique_tags": {"terms": {"field": "tags", "size": 1000}}},
    }

    try:
        response = client.search(index=INDEX_NAME, body=agg_query)
        if response.get("hits", {}).get("total", {}).get("value", 0) > 0:
            aggs = response.get("aggregations", {})
            tags_agg = aggs.get("unique_tags", {})
            return [bucket["key"] for bucket in tags_agg.get("buckets", [])]
        return []
    except Exception as e:
        logger.error(f"Failed to get tags: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch tags")
