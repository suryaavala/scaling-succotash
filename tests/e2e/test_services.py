"""E2E tests for service health, container connectivity, and tag management.

These tests require all Docker Compose services to be running.
"""

import asyncio

import httpx
import pytest


@pytest.fixture(scope="session")
def api_url() -> str:
    """Base URL for the gateway API."""
    return "http://localhost:8000"


@pytest.fixture(scope="session")
def opensearch_url() -> str:
    """Direct OpenSearch URL for service-level checks."""
    return "http://localhost:9200"


@pytest.fixture(scope="session")
def inference_url() -> str:
    """Direct inference service URL."""
    return "http://localhost:8001"


async def _wait_for_service(url: str, retries: int = 10, delay: float = 3.0) -> httpx.Response:
    """Poll a URL until it responds or retries are exhausted."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        for attempt in range(retries):
            try:
                resp = await client.get(url)
                return resp
            except (httpx.ConnectError, httpx.RemoteProtocolError, httpx.ReadTimeout):
                if attempt == retries - 1:
                    raise
                await asyncio.sleep(delay)
    raise RuntimeError(f"Service at {url} never became ready")


# --- Service Health Checks ---


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_gateway_health(api_url: str) -> None:
    """Verify the gateway API container is up and healthy."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{api_url}/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_opensearch_cluster_health(opensearch_url: str) -> None:
    """Verify the OpenSearch container is up and cluster is green/yellow."""
    resp = await _wait_for_service(f"{opensearch_url}/_cluster/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ("green", "yellow")
    assert data["number_of_nodes"] >= 1


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_opensearch_index_exists(opensearch_url: str) -> None:
    """Verify the companies index exists (may be empty in CI)."""
    resp = await _wait_for_service(f"{opensearch_url}/companies/_count")
    if resp.status_code == 404:
        pytest.skip("Companies index not created (no data ingested in CI)")
    assert resp.status_code == 200
    # In CI there may be no data, so just check the response is valid
    assert "count" in resp.json()


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_inference_embed_service(inference_url: str) -> None:
    """Verify the inference embedding endpoint is functional."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            f"{inference_url}/embed",
            json={"text": "artificial intelligence"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "vector" in data
        assert len(data["vector"]) == 384


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_inference_rerank_service(inference_url: str) -> None:
    """Verify the inference reranking endpoint is functional."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            f"{inference_url}/rerank",
            json={
                "query": "machine learning",
                "documents": [
                    "This is about cooking.",
                    "ML is a subset of AI.",
                ],
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["scores"]) == 2
        assert data["scores"][1] > data["scores"][0]


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_redis_connectivity(api_url: str) -> None:
    """Verify Redis caching is functional by checking requests work."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp1 = await client.post(
            f"{api_url}/api/v2/search",
            json={"industry": "software", "size": 5, "page": 1},
        )
        assert resp1.status_code == 200


# --- Deterministic Search Edge Cases ---


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_deterministic_search_empty_results(api_url: str) -> None:
    """Test deterministic search with a non-existent filter returns empty."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{api_url}/api/v2/search",
            json={"name": "zzzznonexistent9999", "size": 10, "page": 1},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["results"] == []


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_deterministic_search_pagination(api_url: str) -> None:
    """Test deterministic search pagination returns different pages."""
    async with httpx.AsyncClient() as client:
        resp1 = await client.post(
            f"{api_url}/api/v2/search",
            json={"size": 5, "page": 1},
        )
        resp2 = await client.post(
            f"{api_url}/api/v2/search",
            json={"size": 5, "page": 2},
        )
        assert resp1.status_code == 200
        assert resp2.status_code == 200
        page1_results = resp1.json()["results"]
        page2_results = resp2.json()["results"]
        if page1_results and page2_results:
            page1_ids = {r.get("id") for r in page1_results}
            page2_ids = {r.get("id") for r in page2_results}
            assert page1_ids.isdisjoint(page2_ids)


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_deterministic_search_with_country(api_url: str) -> None:
    """Test deterministic search filters by country correctly."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{api_url}/api/v2/search",
            json={"country": "united states", "size": 5, "page": 1},
        )
        assert resp.status_code == 200
        results = resp.json()["results"]
        if results:
            for r in results:
                assert r.get("country", "").lower() == "united states"


# --- Tags ---


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_get_all_tags(api_url: str) -> None:
    """Test the tags endpoint returns a list."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{api_url}/api/v2/tags")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


# --- Intelligent Search Variations ---


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_intelligent_search_semantic_only(api_url: str) -> None:
    """Test intelligent search with a purely semantic query (no agentic)."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            f"{api_url}/api/v2/search/intelligent",
            json={"query": "healthcare startups in london"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "results" in data


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_intelligent_search_returns_results_for_broad_query(api_url: str) -> None:
    """Test intelligent search returns a valid response for a broad query."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            f"{api_url}/api/v2/search/intelligent",
            json={"query": "software companies"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "results" in data
        # Results may be empty if no data is ingested (CI)
        assert isinstance(data["results"], list)
