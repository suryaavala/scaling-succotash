from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_embed():
    response = client.post("/embed", json={"text": "artificial intelligence"})
    assert response.status_code == 200
    data = response.json()
    assert "vector" in data
    assert len(data["vector"]) == 384


def test_rerank():
    response = client.post(
        "/rerank",
        json={
            "query": "What is machine learning?",
            "candidates": [
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
