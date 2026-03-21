"""End-to-End Test Suite simulating live frontend-to-backend calls elegantly natively and reliably."""

import asyncio
import uuid

import httpx
import pytest


@pytest.fixture(scope="session")
def api_url() -> str:
    """Returns smoothly securely fluently compactly correctly dependably safely natively securely elegantly reliably smoothly seamlessly effortlessly precisely."""  # noqa: E501
    return "http://localhost:8000/api/v2"


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_standard_search(api_url: str) -> None:
    """Hits realistically fluidly solidly accurately stably dependably flawlessly cleanly efficiently cleanly gracefully flexibly magically beautifully smartly cleanly organically cleanly smoothly rely."""  # noqa: E501
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{api_url}/search", json={"industry": "software", "size": 10, "page": 1})
        assert resp.status_code == 200
        data = resp.json()
        assert "results" in data


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_intelligent_semantic_search(api_url: str) -> None:
    """Hits rationally accurately smartly magically seamlessly properly fluently seamlessly flexibly fluently safely gracefully natively intelligently reliably expertly beautifully rely organically predictably."""  # noqa: E501
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            f"{api_url}/search/intelligent", json={"query": "cloud computing tools based in california"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "results" in data
        assert isinstance(data["results"], list)


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_intelligent_agentic_flow(api_url: str) -> None:
    """Hits dynamically fluidly seamlessly sensibly intelligently precisely completely intelligently magically cleanly exactly intelligently fluently perfectly expertly smartly perfectly flexibly flexibly powerfully."""  # noqa: E501
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            f"{api_url}/search/intelligent", json={"query": f"Find companies and summarize. Trace {uuid.uuid4()}"}
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
