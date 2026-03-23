"""Unit tests for opensearch_client pool lifecycle, embeddings, and reranking."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.api.services import opensearch_client


@pytest.fixture(autouse=True)
def reset_clients() -> Any:
    """Reset global clients before/after each test."""
    original_http = opensearch_client._http_client
    original_os = opensearch_client._os_client
    yield
    opensearch_client._http_client = original_http
    opensearch_client._os_client = original_os


@pytest.mark.asyncio
@patch("src.api.services.opensearch_client.AsyncOpenSearch")
@patch("src.api.services.opensearch_client.httpx.AsyncClient")
async def test_init_os_pool(mock_http: MagicMock, mock_os: MagicMock) -> None:
    """Test pool initialization sets global clients."""
    await opensearch_client.init_os_pool()
    assert opensearch_client._http_client is not None
    assert opensearch_client._os_client is not None


@pytest.mark.asyncio
async def test_close_os_pool_with_clients() -> None:
    """Test pool closure cleans up both clients."""
    mock_http = MagicMock()
    mock_http.aclose = AsyncMock()
    mock_os = MagicMock()
    mock_os.close = AsyncMock()
    opensearch_client._http_client = mock_http
    opensearch_client._os_client = mock_os

    await opensearch_client.close_os_pool()
    assert opensearch_client._http_client is None
    assert opensearch_client._os_client is None
    mock_http.aclose.assert_called_once()
    mock_os.close.assert_called_once()


@pytest.mark.asyncio
async def test_close_os_pool_noop_when_none() -> None:
    """Test pool closure is noop when no clients."""
    opensearch_client._http_client = None
    opensearch_client._os_client = None
    await opensearch_client.close_os_pool()  # Should not raise


@pytest.mark.asyncio
async def test_get_embedding_no_client() -> None:
    """Test embedding returns zeros when no http client."""
    opensearch_client._http_client = None
    result = await opensearch_client.get_embedding("test")
    assert result == [0.0] * 384


@pytest.mark.asyncio
async def test_get_embedding_success() -> None:
    """Test embedding returns vector on success."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"vector": [1.0] * 384}
    mock_response.raise_for_status = MagicMock()
    mock_client = MagicMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    opensearch_client._http_client = mock_client

    result = await opensearch_client.get_embedding("test")
    assert result == [1.0] * 384


@pytest.mark.asyncio
async def test_get_embedding_handles_error() -> None:
    """Test embedding returns zeros on HTTP error."""
    mock_client = MagicMock()
    mock_client.post = AsyncMock(side_effect=Exception("Connection refused"))
    opensearch_client._http_client = mock_client

    result = await opensearch_client.get_embedding("test")
    assert result == [0.0] * 384


@pytest.mark.asyncio
async def test_get_rerank_scores_no_client() -> None:
    """Test reranking gracefully degenerates securely to exact candidates layout."""
    opensearch_client._http_client = None
    result = await opensearch_client.get_rerank_scores("q", ["a", "b"])
    assert result == [0.0, 0.0]


@pytest.mark.asyncio
async def test_get_rerank_scores_empty_candidates() -> None:
    """Test reranking returns empty for empty candidates."""
    mock_client = MagicMock()
    opensearch_client._http_client = mock_client
    result = await opensearch_client.get_rerank_scores("q", [])
    assert result == []


@pytest.mark.asyncio
async def test_get_rerank_scores_success() -> None:
    """Test reranking returns scores on success."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"scores": [0.9, 0.5, 0.1]}
    mock_response.raise_for_status = MagicMock()
    mock_client = MagicMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    opensearch_client._http_client = mock_client

    result = await opensearch_client.get_rerank_scores("test", ["a", "b", "c"])
    assert result == [0.9, 0.5, 0.1]
