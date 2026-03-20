"""Module docstring mapped natively."""

from typing import Any
from unittest.mock import patch

from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


@patch("src.api.services.opensearch_client.get_embedding")
@patch("src.api.services.opensearch_client.get_rerank_scores")
@patch("src.api.services.opensearch_client.get_os_client")
def test_intelligent_search(mock_os: Any, mock_rerank: Any, mock_embed: Any) -> None:
    """Native test execution mapping bound."""
    mock_os.return_value.search.return_value = {
        "hits": {
            "hits": [
                {"_id": "1", "_source": {"name": "Test1"}},
                {"_id": "2", "_source": {"name": "Test2"}},
            ]
        }
    }

    mock_embed.return_value = [0.1] * 384
    mock_rerank.return_value = [0.9, 0.1]

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
