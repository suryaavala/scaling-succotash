"""Frontend functionality tests using Streamlit AppTest."""

from unittest.mock import patch
from streamlit.testing.v1 import AppTest
import requests

@patch("requests.get")
def test_frontend_clear_state(mock_get) -> None:
    """Verify the Clear Search button resets session state."""
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = ["tag1"]

    at = AppTest.from_file("src/frontend/app.py").run()
    
    # Simulate a search by setting session states
    at.session_state.query = "test query"
    at.session_state.results = [{"id": "1", "name": "Company"}]
    at.session_state.agent_answer = "Found some news"
    
    # Trigger the Clear Search button using the explicit key
    at.button(key="btn_clear_ui").click().run()
    
    # Assert states were cleared
    assert at.session_state.query == ""
    assert at.session_state.results == []
    assert at.session_state.agent_answer is None
    assert at.session_state.diagnostics is None
    assert at.session_state.agent_markdown is None


@patch("requests.post")
@patch("requests.get")
def test_frontend_deterministic_search(mock_get, mock_post) -> None:
    """Verify deterministic search routing and parsing."""
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = ["tag1", "tag2"]
    
    at = AppTest.from_file("src/frontend/app.py").run()
    
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {
        "results": [{"id": "1", "name": "MockCompany", "industry": "Tech", "tags": ["tag1"]}],
        "diagnostics": {"route": "Deterministic", "scores": []}
    }
    
    # Set inputs and submit deterministic filter by known key
    at.text_input(key="filter_name_ui").set_value("MockCompany")
    
    # Apply Filters button
    at.button(key="btn_apply_filters_ui").click().run()
    
    assert len(at.session_state.results) == 1
    assert at.session_state.results[0]["name"] == "MockCompany"
    assert at.session_state.diagnostics["route"] == "Deterministic"


@patch("requests.post")
@patch("requests.get")
@patch("time.sleep", return_value=None)
def test_frontend_intelligent_search_agentic_flow(mock_sleep, mock_get, mock_post) -> None:
    """Verify agentic flow mapping in frontend."""
    
    def mock_get_behavior(*args, **kwargs):
        class MockResponse:
            def __init__(self, json_data, status_code=200):
                self._json_data = json_data
                self.status_code = status_code
            def json(self):
                return self._json_data
        
        url = args[0]
        if "tags" in url:
            return MockResponse(["tag1"])
        if "agentic" in url:
            return MockResponse({"status": "SUCCESS", "result": {"summary": "Mock Insight", "raw_markdown": "Mock MD"}})
        return MockResponse({})

    mock_get.side_effect = mock_get_behavior
    
    at = AppTest.from_file("src/frontend/app.py").run()
    
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {
        "results": [{"id": "2", "name": "AI Company", "industry": "AI"}],
        "agentic_task_id": "mock_task_123",
        "diagnostics": {"route": "AgenticSearch", "scores": [{"knn_score": 1.0}]}
    }
    
    # Execute intelligent search
    at.text_input(key="intelligent_input_ui").set_value("AI companies")
    
    # form_submit_button maps to AppTest.button identically but doesn't take keys well sometimes if unnamed,
    # Let's see if we can use label
    search_btn = [btn for btn in at.button if btn.label == "Search"][0]
    search_btn.click().run()
        
    assert at.session_state.agent_answer == "Mock Insight"
    assert at.session_state.agent_markdown == "Mock MD"
    assert len(at.session_state.results) == 1


@patch("requests.post")
@patch("requests.get")
def test_frontend_intelligent_search_failure(mock_get, mock_post) -> None:
    """Verify intelligent search failure resets gracefully."""
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = []
    
    mock_post.side_effect = requests.exceptions.ConnectionError("Offline")
    
    at = AppTest.from_file("src/frontend/app.py").run()
    
    at.text_input(key="intelligent_input_ui").set_value("AI companies")
    search_btn = [btn for btn in at.button if btn.label == "Search"][0]
    search_btn.click().run()
    
    assert len(at.error) > 0
    assert "Failed to connect to Intelligent API" in at.error[0].value
