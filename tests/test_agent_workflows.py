"""Unit tests for Celery agent workflows."""

from typing import Any
from unittest.mock import MagicMock, patch

import json
from celery.exceptions import Retry
from src.worker.agent_workflows import DLQTask, search_recent_news, synthesize_agent_response


def test_search_recent_news_with_domain() -> None:
    """Test news retrieval with a valid domain."""
    result = search_recent_news("acme.com")
    assert "acme.com" in result
    assert "Series A" in result


def test_search_recent_news_no_domain() -> None:
    """Test news retrieval with no domain returns fallback."""
    result = search_recent_news(None)
    assert result == "No recent news available."


def test_search_recent_news_empty_domain() -> None:
    """Test news retrieval with empty string domain."""
    result = search_recent_news("")
    assert result == "No recent news available."


def test_synthesize_empty_candidates() -> None:
    """Test synthesis with empty candidates returns early."""
    result = synthesize_agent_response("test query", [])
    assert result["summary"] == "No relevant companies found to perform external search on."


@patch("src.worker.agent_workflows.completion")
def test_synthesize_with_candidates(mock_completion: MagicMock) -> None:
    """Test synthesis builds context and calls LLM."""
    mock_msg = MagicMock()
    mock_msg.content = "Summary of Acme Corp findings."
    mock_choice = MagicMock()
    mock_choice.message = mock_msg
    mock_completion.return_value = MagicMock(choices=[mock_choice])

    candidates: list[dict[str, Any]] = [
        {"name": "Acme Corp", "industry": "Software", "website": "acme.com"},
        {"name": "Beta Inc", "industry": "Finance", "website": None},
    ]
    result = synthesize_agent_response("find software companies", candidates)
    assert result["summary"] == "Summary of Acme Corp findings."
    mock_completion.assert_called_once()


@patch("src.worker.agent_workflows.completion")
@patch("src.worker.agent_workflows.synthesize_agent_response.retry")
def test_synthesize_handles_llm_error(mock_retry: MagicMock, mock_completion: MagicMock) -> None:
    """Test synthesis triggers retry gracefully upon LLM failure."""
    mock_completion.side_effect = Exception("LLM timeout")
    
    # We mock self.retry so that we don't depend on Celery's sync-mode exception behavior
    mock_retry.side_effect = Retry("Simulated retry")
    
    candidates: list[dict[str, Any]] = [
        {"name": "Acme Corp", "industry": "Software", "website": "acme.com"},
    ]
    
    try:
        synthesize_agent_response("test", candidates)
        assert False, "Should have raised Retry"
    except Retry:
        assert mock_completion.call_count == 1
        mock_retry.assert_called_once()


@patch("src.worker.agent_workflows.redis.Redis.from_url")
def test_dlq_task_on_failure(mock_redis: MagicMock) -> None:
    """Test the native DLQ Task pushes payloads dynamically."""
    mock_client = MagicMock()
    mock_redis.return_value = mock_client
    
    task = DLQTask()
    task.name = "test_bound"
    exc = Exception("Catastrophic error")
    
    mock_einfo = MagicMock()
    mock_einfo.traceback = "Traceback details..."
    
    task.on_failure(exc, "task-123", ("arg1",), {"kw": "val"}, mock_einfo)
    
    mock_client.lpush.assert_called_once()
    args, _ = mock_client.lpush.call_args
    assert args[0] == "celery:dlq"
    payload = json.loads(args[1])
    
    assert payload["task_id"] == "task-123"
    assert payload["exception"] == "Catastrophic error"
    assert payload["args"] == ["arg1"]


@patch("src.worker.agent_workflows.completion")
def test_synthesize_handles_none_content(mock_completion: MagicMock) -> None:
    """Test synthesis handles None LLM content."""
    mock_msg = MagicMock()
    mock_msg.content = None
    mock_choice = MagicMock()
    mock_choice.message = mock_msg
    mock_completion.return_value = MagicMock(choices=[mock_choice])

    candidates: list[dict[str, Any]] = [
        {"name": "Acme Corp", "industry": "Software"},
    ]
    result = synthesize_agent_response("test", candidates)
    assert result["summary"] == "No summary generated."
