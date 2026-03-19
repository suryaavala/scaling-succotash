import pytest
from fastapi.testclient import TestClient
from gateway_api.app.main import app
from unittest.mock import patch

client = TestClient(app)

@patch('gateway_api.app.services.opensearch_client.get_embedding')
@patch('gateway_api.app.services.opensearch_client.get_rerank_scores')
@patch('gateway_api.app.services.opensearch_client.get_opensearch_client')
def test_intelligent_search(mock_os, mock_rerank, mock_embed):
    mock_os.return_value.search.return_value = {
        "hits": {
            "hits": [
                {"_id": "1", "_source": {"name": "Test1"}},
                {"_id": "2", "_source": {"name": "Test2"}}
            ]
        }
    }
    
    mock_embed.return_value = [0.1] * 384
    mock_rerank.return_value = [0.9, 0.1]
    
    with patch('gateway_api.app.services.llm_router.extract_intent', return_value={"requires_agent": False}):
        resp = client.post("/api/v2/search/intelligent", json={"query": "test query"})
        
    assert resp.status_code == 200
    data = resp.json()
    assert "results" in data
    assert len(data["results"]) == 2
    assert data["results"][0]["name"] == "Test1"
