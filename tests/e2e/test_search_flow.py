"""End-to-End Test Suite simulating live frontend-to-backend calls."""

import asyncio
import os
import uuid

import httpx
import pytest


@pytest.fixture(scope="session")
def api_url() -> str:
    """Base URL for the gateway API v2 endpoints."""
    return "http://localhost:8000/api/v2"


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_standard_search(api_url: str) -> None:
    """Test deterministic search endpoint returns results."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{api_url}/search", json={"industry": "software", "size": 10, "page": 1})
        assert resp.status_code == 200
        data = resp.json()
        assert "results" in data


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_intelligent_semantic_search(api_url: str) -> None:
    """Test intelligent search endpoint returns semantic results."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            f"{api_url}/search/intelligent", json={"query": "cloud computing tools based in california"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "results" in data
        assert isinstance(data["results"], list)


@pytest.mark.e2e
@pytest.mark.asyncio
@pytest.mark.skipif(not os.getenv("GEMINI_API_KEY"), reason="GEMINI_API_KEY not set")
async def test_intelligent_agentic_flow(api_url: str) -> None:
    """Test agentic flow dispatches a Celery task and polls for results."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            f"{api_url}/search/intelligent", json={"query": f"latest acquisitions by microsoft in ai. Trace {uuid.uuid4()}"}
        )
        assert resp.status_code == 200
        data = resp.json()
        task_id = data.get("agentic_task_id")
        assert task_id is not None

        for _ in range(20):
            await asyncio.sleep(2)
            poll_resp = await client.get(f"{api_url}/search/agentic/{task_id}")
            if poll_resp.status_code == 200:
                poll_data = poll_resp.json()
                if poll_data.get("status") == "SUCCESS":
                    assert poll_data.get("result") is not None
                    return
                elif poll_data.get("status") == "FAILURE":
                    pytest.fail("Agentic Task failed!")

        pytest.fail("Polling timed out!")
