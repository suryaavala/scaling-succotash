"""Unit tests for the Gateway API search endpoints."""

from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from src.api.main import app
from src.api.services.opensearch_client import get_company_repository

client = TestClient(app)


def test_intelligent_search() -> None:
    """Test intelligent search endpoint returns semantic results."""
    mock_repo = MagicMock()
    mock_repo.two_stage_retrieval = AsyncMock(
        return_value=[
            {"id": "1", "name": "Test1"},
            {"id": "2", "name": "Test2"},
        ]
    )

    app.dependency_overrides[get_company_repository] = lambda: mock_repo

    with patch(
        "src.api.services.llm_router.LLMClient.extract_intent",
        return_value=({"requires_agent": False}, False),
    ):
        resp = client.post("/api/v2/search/intelligent", json={"query": "test query"})

    assert resp.status_code == 200
    data = resp.json()
    assert "results" in data
    assert len(data["results"]) == 2
    assert data["results"][0]["name"] == "Test1"

    app.dependency_overrides.clear()
