"""Unit tests for the OpenSearchCompanyRepository."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.api.services.opensearch_client import OpenSearchCompanyRepository


@pytest.fixture
def mock_os_client() -> MagicMock:
    """Create a mock AsyncOpenSearch client."""
    return MagicMock()


@pytest.fixture
def repo(mock_os_client: MagicMock) -> OpenSearchCompanyRepository:
    """Create a repository with a mock client."""
    r = OpenSearchCompanyRepository()
    r.client = mock_os_client
    return r


@pytest.mark.asyncio
async def test_search_returns_results(repo: OpenSearchCompanyRepository) -> None:
    """Test search returns formatted results with IDs."""
    repo.client.search = AsyncMock(
        return_value={
            "hits": {
                "hits": [
                    {"_id": "1", "_source": {"name": "Acme Corp", "industry": "software"}},
                    {"_id": "2", "_source": {"name": "Beta Inc", "industry": "finance"}},
                ]
            }
        }
    )
    dsl: dict[str, Any] = {"query": {"match_all": {}}}
    results = await repo.search(dsl)
    assert len(results) == 2
    assert results[0]["id"] == "1"
    assert results[0]["name"] == "Acme Corp"
    assert results[1]["id"] == "2"


@pytest.mark.asyncio
async def test_search_returns_empty_on_no_client() -> None:
    """Test search returns empty list when client is None."""
    repo = OpenSearchCompanyRepository()
    repo.client = None
    results = await repo.search({"query": {"match_all": {}}})
    assert results == []


@pytest.mark.asyncio
async def test_search_returns_empty_on_error(repo: OpenSearchCompanyRepository) -> None:
    """Test search returns empty list on exception."""
    repo.client.search = AsyncMock(side_effect=Exception("Connection failed"))
    results = await repo.search({"query": {"match_all": {}}})
    assert results == []


@pytest.mark.asyncio
async def test_two_stage_retrieval_returns_empty_on_no_client() -> None:
    """Test two_stage_retrieval returns empty when client is None."""
    repo = OpenSearchCompanyRepository()
    repo.client = None
    results = await repo.two_stage_retrieval("query", {}, [0.0] * 384)
    assert results == []


@pytest.mark.asyncio
async def test_two_stage_retrieval_returns_results(repo: OpenSearchCompanyRepository) -> None:
    """Test two_stage_retrieval returns reranked results."""
    repo.client.search = AsyncMock(
        return_value={
            "hits": {
                "hits": [
                    {"_id": "1", "_source": {"name": "Acme", "industry": "tech", "locality": "SF"}, "_score": 1.0},
                    {"_id": "2", "_source": {"name": "Beta", "industry": "fin", "locality": "NY"}, "_score": 0.5},
                ]
            }
        }
    )
    with patch(
        "src.api.services.opensearch_client.get_rerank_scores",
        new_callable=AsyncMock,
        return_value=[0.8, 0.9],
    ):
        results = await repo.two_stage_retrieval("test", {"industry": "tech"}, [0.0] * 384)
    assert len(results) == 2
    # Beta should be first after reranking (score 0.9 > 0.8)
    assert results[0]["id"] == "2"


@pytest.mark.asyncio
async def test_two_stage_retrieval_empty_hits(repo: OpenSearchCompanyRepository) -> None:
    """Test two_stage_retrieval returns empty when no hits."""
    repo.client.search = AsyncMock(return_value={"hits": {"hits": []}})
    results = await repo.two_stage_retrieval("query", {}, [0.0] * 384)
    assert results == []


@pytest.mark.asyncio
async def test_two_stage_retrieval_handles_rerank_error(repo: OpenSearchCompanyRepository) -> None:
    """Test two_stage_retrieval still returns results when reranking fails."""
    repo.client.search = AsyncMock(
        return_value={
            "hits": {
                "hits": [
                    {"_id": "1", "_source": {"name": "Acme", "industry": "tech", "locality": "SF"}, "_score": 1.0},
                ]
            }
        }
    )
    with patch(
        "src.api.services.opensearch_client.get_rerank_scores",
        new_callable=AsyncMock,
        side_effect=Exception("Inference down"),
    ):
        results = await repo.two_stage_retrieval("test", {}, [0.0] * 384)
    assert len(results) == 1
    assert results[0]["name"] == "Acme"


@pytest.mark.asyncio
async def test_add_tag(repo: OpenSearchCompanyRepository) -> None:
    """Test add_tag calls OpenSearch update."""
    repo.client.update = AsyncMock(return_value={"result": "updated"})
    result = await repo.add_tag("123", "priority")
    assert result["status"] == "success"
    assert result["tag"] == "priority"
    repo.client.update.assert_called_once()


@pytest.mark.asyncio
async def test_get_all_tags_with_results(repo: OpenSearchCompanyRepository) -> None:
    """Test get_all_tags returns tag names."""
    repo.client.search = AsyncMock(
        return_value={
            "hits": {"total": {"value": 5}},
            "aggregations": {"unique_tags": {"buckets": [{"key": "priority"}, {"key": "vip"}]}},
        }
    )
    tags = await repo.get_all_tags()
    assert tags == ["priority", "vip"]


@pytest.mark.asyncio
async def test_get_all_tags_empty(repo: OpenSearchCompanyRepository) -> None:
    """Test get_all_tags returns empty when no documents."""
    repo.client.search = AsyncMock(return_value={"hits": {"total": {"value": 0}}})
    tags = await repo.get_all_tags()
    assert tags == []
