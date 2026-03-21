"""Module docstring mapped natively."""

from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from src.api.main import app
from src.api.services.opensearch_client import get_os_client

client = TestClient(app)


def test_intelligent_search() -> None:
    """Native test execution mapping bound."""
    mock_os_client = MagicMock()
    mock_os_client.two_stage_retrieval = AsyncMock(
        return_value=[
            {"id": "1", "name": "Test1"},
            {"id": "2", "name": "Test2"},
        ]
    )

    app.dependency_overrides[get_os_client] = lambda: mock_os_client

    with patch(
        "src.api.services.llm_router.LLMClient.extract_intent",
        return_value={"requires_agent": False},
    ):
        resp = client.post("/api/v2/search/intelligent", json={"query": "test query"})

    assert resp.status_code == 200
    data = resp.json()
    assert "results" in data
    assert len(data["results"]) == 2
    assert data["results"][0]["name"] == "Test1"

    app.dependency_overrides.clear()
