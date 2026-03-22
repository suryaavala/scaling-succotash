"""Unit tests for Tags endpoint and search strategies."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.api.models.schemas import IntelligentSearchResponse
from src.api.services.opensearch_client import get_company_repository
from src.api.services.search_strategies import (
    AgenticSearchStrategy,
    DeterministicSearchStrategy,
    SearchContext,
    SemanticSearchStrategy,
)

# --- Tags endpoint tests ---

client = TestClient(app)


def test_add_tag_success() -> None:
    """Test adding a tag returns success."""
    mock_repo = MagicMock()
    mock_repo.add_tag = AsyncMock(return_value={"status": "success", "tag": "priority", "company_id": "1"})
    app.dependency_overrides[get_company_repository] = lambda: mock_repo
    resp = client.post("/api/v2/companies/1/tags", json={"tag": "priority"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "success"
    app.dependency_overrides.clear()


def test_add_tag_not_found() -> None:
    """Test adding a tag to non-existent company returns 404."""
    from opensearchpy.exceptions import NotFoundError

    mock_repo = MagicMock()
    mock_repo.add_tag = AsyncMock(side_effect=NotFoundError(404, "not found"))
    app.dependency_overrides[get_company_repository] = lambda: mock_repo
    resp = client.post("/api/v2/companies/999/tags", json={"tag": "test"})
    assert resp.status_code == 404
    app.dependency_overrides.clear()


def test_add_tag_server_error() -> None:
    """Test adding a tag handles server errors as 500."""
    mock_repo = MagicMock()
    mock_repo.add_tag = AsyncMock(side_effect=Exception("DB error"))
    app.dependency_overrides[get_company_repository] = lambda: mock_repo
    resp = client.post("/api/v2/companies/1/tags", json={"tag": "test"})
    assert resp.status_code == 500
    app.dependency_overrides.clear()


def test_get_all_tags_success() -> None:
    """Test getting all tags returns list."""
    mock_repo = MagicMock()
    mock_repo.get_all_tags = AsyncMock(return_value=["priority", "vip"])
    app.dependency_overrides[get_company_repository] = lambda: mock_repo
    resp = client.get("/api/v2/tags")
    assert resp.status_code == 200
    assert resp.json() == ["priority", "vip"]
    app.dependency_overrides.clear()


def test_get_all_tags_error() -> None:
    """Test getting tags handles errors as 500."""
    mock_repo = MagicMock()
    mock_repo.get_all_tags = AsyncMock(side_effect=Exception("DB error"))
    app.dependency_overrides[get_company_repository] = lambda: mock_repo
    resp = client.get("/api/v2/tags")
    assert resp.status_code == 500
    app.dependency_overrides.clear()


# --- Search strategy tests ---


@pytest.mark.asyncio
async def test_semantic_strategy_returns_candidates() -> None:
    """Test SemanticSearchStrategy returns candidates directly."""
    strategy = SemanticSearchStrategy()
    candidates = [{"id": "1", "name": "Acme"}]
    result = await strategy.execute("test", candidates)
    assert isinstance(result, IntelligentSearchResponse)
    assert len(result.results) == 1
    assert result.agentic_task_id is None


@pytest.mark.asyncio
async def test_agentic_strategy_returns_task_id() -> None:
    """Test AgenticSearchStrategy dispatches to Celery and returns task ID."""
    strategy = AgenticSearchStrategy()
    candidates = [{"id": "1", "name": "Acme"}]
    with MagicMock() as mock_celery:
        mock_celery.id = "task-123"
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(
                "src.api.services.search_strategies.dispatch_agentic_search",
                AsyncMock(return_value={"task_id": "task-123", "status": "processing"}),
            )
            result = await strategy.execute("test", candidates)
    assert result.agentic_task_id == "task-123"
    assert len(result.results) == 1


@pytest.mark.asyncio
async def test_search_context_delegates_to_strategy() -> None:
    """Test SearchContext delegates to the configured strategy."""
    strategy = SemanticSearchStrategy()
    context = SearchContext(strategy)
    candidates = [{"id": "1"}, {"id": "2"}]
    result = await context.execute_search("test", candidates)
    assert len(result.results) == 2


@pytest.mark.asyncio
async def test_deterministic_strategy_builds_dsl() -> None:
    """Test DeterministicSearchStrategy calls repository.search."""
    from src.api.models.schemas import SearchRequest

    strategy = DeterministicSearchStrategy()
    mock_repo = MagicMock()
    mock_repo.search = AsyncMock(return_value=[{"id": "1", "name": "Test", "industry": "software"}])
    request = SearchRequest(industry="software", size=5, page=1)
    result = await strategy.execute(request, mock_repo)
    assert len(result.results) == 1
    mock_repo.search.assert_called_once()
