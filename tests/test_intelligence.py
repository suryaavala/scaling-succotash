from unittest.mock import patch

from app.services.llm_router import extract_intent


@patch("app.services.llm_router.completion")
def test_extract_intent_deterministic(mock_completion):
    class MockMessage:
        content = '{"requires_agent": false, "industry": "technology", "country": "us"}'

    class MockChoice:
        message = MockMessage()

    class MockResponse:
        choices = [MockChoice()]

    mock_completion.return_value = MockResponse()

    intent = extract_intent("tech companies in us")
    assert intent["industry"] == "technology"
    assert intent["country"] == "us"
    assert intent["requires_agent"] is False
