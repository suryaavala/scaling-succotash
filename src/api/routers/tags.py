"""Tag management endpoints using the CompanyRepository."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from opensearchpy.exceptions import NotFoundError

from src.api.domain.interfaces import CompanyRepository
from src.api.models.schemas import TagRequest
from src.api.services.opensearch_client import get_company_repository

router = APIRouter(prefix="/api/v2", tags=["Tags"])
logger = logging.getLogger("api")


@router.post("/companies/{company_id}/tags")
async def add_tag(
    company_id: str,
    request: TagRequest,
    repo: CompanyRepository = Depends(get_company_repository),
) -> dict[str, str]:
    """Add a tag to a company document."""
    tag = request.tag.strip()
    try:
        return await repo.add_tag(company_id, tag)
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Company not found")
    except Exception as e:
        logger.error(f"Failed to update tag: {e}")
        raise HTTPException(status_code=500, detail="Failed to add tag")


@router.get("/tags")
async def get_all_tags(
    repo: CompanyRepository = Depends(get_company_repository),
) -> list[str]:
    """Retrieve all unique tags across the index."""
    try:
        return await repo.get_all_tags()
    except Exception as e:
        logger.error(f"Failed to get tags: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch tags")
