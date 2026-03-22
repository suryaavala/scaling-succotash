"""Unit tests for Celery agent workflows."""

from typing import Any
from unittest.mock import MagicMock, patch

from src.worker.agent_workflows import search_recent_news, synthesize_agent_response


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
def test_synthesize_handles_llm_error(mock_completion: MagicMock) -> None:
    """Test synthesis handles LLM failure gracefully."""
    mock_completion.side_effect = Exception("LLM timeout")
    candidates: list[dict[str, Any]] = [
        {"name": "Acme Corp", "industry": "Software", "website": "acme.com"},
    ]
    result = synthesize_agent_response("test", candidates)
    assert result["summary"] == "Error synthesizing agent response."


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
