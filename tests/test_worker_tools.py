"""Worker task tool functionality testing mapped natively."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from src.worker.tools.search import fetch_recent_company_news


@pytest.fixture
def mock_settings() -> MagicMock:
    """Fixture bypassing configurations."""
    mock = MagicMock()
    mock.redis_url = "redis://localhost:6379/1"
    mock.search_api_key = "tvly-mock-key"
    return mock


@pytest.mark.asyncio
@patch("src.worker.tools.search.get_settings")
@patch("src.worker.tools.search.httpx.AsyncClient.post", new_callable=AsyncMock)
@patch("src.worker.tools.search.redis.Redis.from_url", new_callable=MagicMock)
async def test_fetch_recent_company_news_cache_miss(mock_redis, mock_post, mock_get_settings, mock_settings) -> None:
    """Validate external news acquisition successfully mapping outputs."""
    mock_get_settings.return_value = mock_settings
    
    mock_redis_instance = AsyncMock()
    mock_redis_instance.get.return_value = None
    mock_redis.return_value = mock_redis_instance

    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "results": [
            {"url": "http://example.com/1", "content": "Company raises series A."},
        ]
    }
    mock_post.return_value = mock_resp

    res = await fetch_recent_company_news("TechCorp techcorp.ai recent news")
    assert "Company raises series A." in res
    assert mock_redis_instance.setex.called


@pytest.mark.asyncio
@patch("src.worker.tools.search.get_settings")
@patch("src.worker.tools.search.httpx.AsyncClient.post", new_callable=AsyncMock)
@patch("src.worker.tools.search.redis.Redis.from_url", new_callable=MagicMock)
async def test_fetch_recent_company_news_cache_hit(mock_redis, mock_post, mock_get_settings, mock_settings) -> None:
    """Validate cache bypass correctly bounds fetching directly."""
    mock_get_settings.return_value = mock_settings
    
    mock_redis_instance = AsyncMock()
    mock_redis_instance.get.return_value = "Cached News Payload"
    mock_redis.return_value = mock_redis_instance

    res = await fetch_recent_company_news("TechCorp techcorp.ai recent news")
    assert res == "Cached News Payload"
    mock_post.assert_not_called()
    assert not mock_redis_instance.setex.called


@pytest.mark.asyncio
@patch("src.worker.tools.search.get_settings")
@patch("src.worker.tools.search.httpx.AsyncClient.post", new_callable=AsyncMock)
@patch("src.worker.tools.search.redis.Redis.from_url", new_callable=MagicMock)
async def test_fetch_recent_company_news_empty(mock_redis, mock_post, mock_get_settings, mock_settings) -> None:
    """Validate graceful parsing executing natively on empty external payloads."""
    mock_get_settings.return_value = mock_settings
    
    mock_redis_instance = AsyncMock()
    mock_redis_instance.get.return_value = None
    mock_redis.return_value = mock_redis_instance

    mock_resp = MagicMock()
    mock_resp.json.return_value = {"results": []}
    mock_post.return_value = mock_resp

    res = await fetch_recent_company_news("EmptyCorp empty.io recent news")
    assert res == "No recent significant news found."


@pytest.mark.asyncio
@patch("src.worker.tools.search.get_settings")
@patch("src.worker.tools.search.httpx.AsyncClient.post", new_callable=AsyncMock)
@patch("src.worker.tools.search.redis.Redis.from_url", new_callable=MagicMock)
async def test_fetch_recent_company_news_http_err(mock_redis, mock_post, mock_get_settings, mock_settings) -> None:
    """Validate timeout interceptions correctly fall back cleanly."""
    mock_get_settings.return_value = mock_settings
    
    mock_redis_instance = AsyncMock()
    mock_redis_instance.get.return_value = None
    mock_redis.return_value = mock_redis_instance

    mock_post.side_effect = httpx.HTTPStatusError("500 Server Error", request=AsyncMock(), response=AsyncMock())

    res = await fetch_recent_company_news("FailCorp fail.io recent news")
    assert res == "External search temporarily unavailable."
