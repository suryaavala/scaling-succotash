"""Module docstring mapped natively."""

from fastapi.testclient import TestClient

from src.inference.main import app

client = TestClient(app)


from unittest.mock import patch, MagicMock

@patch("src.inference.main.get_embedding_model")
def test_embed(mock_get_model) -> None:
    """Native test execution mapping bound."""
    mock_model = MagicMock()
    mock_model.encode.return_value.tolist.return_value = [0.1] * 384
    mock_get_model.return_value = mock_model
    
    response = client.post("/embed", json={"text": "artificial intelligence"})
    assert response.status_code == 200
    data = response.json()
    assert "vector" in data
    assert len(data["vector"]) == 384


@patch("src.inference.main.get_reranker_model")
def test_rerank(mock_get_model) -> None:
    """Native test execution mapping bound."""
    mock_model = MagicMock()
    mock_model.predict.return_value.tolist.return_value = [0.1, 0.9, 0.2]
    mock_get_model.return_value = mock_model
    
    response = client.post(
        "/rerank",
        json={
            "query": "What is machine learning?",
            "documents": [
                "Apple is a fruit.",
                "Machine learning is a subset of AI.",
                "Cars have four wheels.",
            ],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "scores" in data
    assert len(data["scores"]) == 3
    # Second candidate is vastly more relevant
    assert data["scores"][1] > data["scores"][0]
    assert data["scores"][1] > data["scores"][2]

def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

@patch("src.inference.main.get_embedding_model")
@patch("src.inference.main.get_reranker_model")
def test_lifespan(mock_get_rerank, mock_get_embed) -> None:
    with TestClient(app) as c:
        pass
