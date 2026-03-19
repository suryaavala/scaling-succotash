import pytest
from unittest.mock import patch
from app.services.intelligence_service import extract_intent, IntentSchema
from app.services.agent_service import synthesize_agent_response
from app.models.schemas import Company

@patch('app.services.intelligence_service.completion')
def test_extract_intent_deterministic(mock_completion):
    class MockMessage:
        content = '{"requires_agent": false, "industry": "technology", "country": "us"}'
    class MockChoice:
        message = MockMessage()
    class MockResponse:
        choices = [MockChoice()]
        
    mock_completion.return_value = MockResponse()
    
    intent = extract_intent("tech companies in us")
    assert intent.industry == "technology"
    assert intent.country == "us"
    assert intent.requires_agent is False

@patch('app.services.agent_service.completion')
def test_synthesize_agent_response(mock_completion):
    class MockMessage:
        content = "The companies raised $10M"
    class MockChoice:
        message = MockMessage()
    class MockResponse:
        choices = [MockChoice()]
        
    mock_completion.return_value = MockResponse()
    
    candidates = [Company(id="1", name="TestCo", domain="test.com")]
    resp = synthesize_agent_response("fundraising", candidates)
    
    assert "raised $10M" in resp
