"""Unit tests for the main API application and async task endpoints."""

from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


def test_health_check() -> None:
    """Test health endpoint returns ok."""
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_deterministic_search_empty() -> None:
    """Test deterministic search with no filters returns results."""
    from src.api.services.opensearch_client import get_company_repository

    mock_repo = MagicMock()
    mock_repo.search = AsyncMock(return_value=[{"id": "1", "name": "Test Corp", "industry": "software"}])
    app.dependency_overrides[get_company_repository] = lambda: mock_repo
    resp = client.post("/api/v2/search", json={"page": 1, "size": 10})
    assert resp.status_code == 200
    assert len(resp.json()["results"]) == 1
    app.dependency_overrides.clear()


def test_dispatch_agentic_search() -> None:
    """Test dispatching an agentic search returns a task ID."""
    mock_task = MagicMock()
    mock_task.id = "test-task-id"
    with patch(
        "src.api.routers.async_tasks.celery_app.send_task",
        return_value=mock_task,
    ):
        resp = client.post(
            "/api/v2",
            json={"query": "test", "candidates": [{"name": "A"}]},
        )
    assert resp.status_code == 200
    assert resp.json()["task_id"] == "test-task-id"


def test_get_task_status_pending() -> None:
    """Test retrieving a pending task status."""
    with patch("src.api.routers.async_tasks.AsyncResult") as mock_async:
        mock_result = MagicMock()
        mock_result.status = "PENDING"
        mock_result.ready.return_value = False
        mock_async.return_value = mock_result
        resp = client.get("/api/v2/search/agentic/some-task-id")
    assert resp.status_code == 200
    assert resp.json()["status"] == "PENDING"


def test_get_task_status_success() -> None:
    """Test retrieving a successful task result."""
    with patch("src.api.routers.async_tasks.AsyncResult") as mock_async:
        mock_result = MagicMock()
        mock_result.status = "SUCCESS"
        mock_result.ready.return_value = True
        mock_result.successful.return_value = True
        mock_result.result = "synthesis complete"
        mock_async.return_value = mock_result
        resp = client.get("/api/v2/search/agentic/some-task-id")
    assert resp.status_code == 200
    assert resp.json()["status"] == "SUCCESS"
    assert resp.json()["result"] == "synthesis complete"


def test_get_task_status_failed() -> None:
    """Test retrieving a failed task status."""
    with patch("src.api.routers.async_tasks.AsyncResult") as mock_async:
        mock_result = MagicMock()
        mock_result.status = "FAILURE"
        mock_result.ready.return_value = True
        mock_result.successful.return_value = False
        mock_result.result = RuntimeError("task crashed")
        mock_async.return_value = mock_result
        resp = client.get("/api/v2/search/agentic/some-task-id")
    assert resp.status_code == 200
    assert resp.json()["status"] == "failed"
