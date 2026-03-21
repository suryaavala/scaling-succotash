"""Module docstring mapped natively."""

from typing import Any
from unittest.mock import patch

import pytest

from src.api.services.llm_router import LLMClient


@pytest.mark.asyncio
@patch("src.api.services.llm_router.acompletion")
async def test_extract_intent_deterministic(mock_completion: Any) -> None:
    """Native test execution mapping bound."""

    class MockMessage:
        content = '{"requires_agent": false, "industry": "technology", "country": "us"}'

    class MockChoice:
        message = MockMessage()

    class MockResponse:
        choices = [MockChoice()]

    mock_completion.return_value = MockResponse()

    client = LLMClient()
    intent, is_cached = await client.extract_intent("tech companies in us")
    assert intent["industry"] == "technology"
    assert intent["country"] == "us"
    assert intent["requires_agent"] is False
