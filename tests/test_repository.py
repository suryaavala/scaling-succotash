"""Unit tests for the OpenSearchCompanyRepository."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.api.services.opensearch_client import (
    OpenSearchCompanyRepository,
    get_embedding,
    get_rerank_scores,
    _fetch_embedding_raw,
    _fetch_rerank_raw,
    init_os_pool,
    close_os_pool,
)
from circuitbreaker import CircuitBreakerError


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


@pytest.mark.asyncio
async def test_fetch_embedding_raw_success() -> None:
    """Test raw inference embedding execution."""
    await init_os_pool()
    with patch("src.api.services.opensearch_client._http_client.post", new_callable=AsyncMock) as mock_post:
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"vector": [1.0, 2.0]}
        mock_post.return_value = mock_resp
        res = await _fetch_embedding_raw("foo")
    assert res == [1.0, 2.0]
    await close_os_pool()


@pytest.mark.asyncio
async def test_fetch_embedding_raw_no_client() -> None:
    """Test runtime error on empty connection pool."""
    import src.api.services.opensearch_client as os_client
    os_client._http_client = None
    with pytest.raises(RuntimeError):
        await _fetch_embedding_raw("foo")


@pytest.mark.asyncio
async def test_get_embedding_circuit_breaker_fallback() -> None:
    """Test embedding degrades safely to zeroed array."""
    with patch("src.api.services.opensearch_client._fetch_embedding_raw", new_callable=AsyncMock, side_effect=CircuitBreakerError):
        emb = await get_embedding("test")
    assert emb == [0.0] * 384


@pytest.mark.asyncio
async def test_fetch_rerank_raw_success() -> None:
    """Test raw rerank scoring execution."""
    await init_os_pool()
    with patch("src.api.services.opensearch_client._http_client.post", new_callable=AsyncMock) as mock_post:
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"scores": [0.9, 0.8]}
        mock_post.return_value = mock_resp
        res = await _fetch_rerank_raw("foo", ["doc1", "doc2"])
    assert res == [0.9, 0.8]
    await close_os_pool()


@pytest.mark.asyncio
async def test_fetch_rerank_raw_invalid() -> None:
    """Test runtime error on empty candidates."""
    with pytest.raises(RuntimeError):
        await _fetch_rerank_raw("foo", [])


@pytest.mark.asyncio
async def test_get_rerank_circuit_breaker_fallback() -> None:
    """Test reranking degrades safely to zeroed scores."""
    with patch("src.api.services.opensearch_client._fetch_rerank_raw", new_callable=AsyncMock, side_effect=CircuitBreakerError):
        scores = await get_rerank_scores("test", ["a", "b"])
    assert scores == [0.0, 0.0]
