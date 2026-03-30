"""Frontend functionality tests using Streamlit AppTest."""

from streamlit.testing.v1 import AppTest

def test_frontend_clear_state() -> None:
    """Verify the Clear Search button resets session state."""
    at = AppTest.from_file("src/frontend/app.py").run()
    
    # Simulate a search by setting session states
    at.session_state.query = "test query"
    at.session_state.results = [{"id": "1", "name": "Company"}]
    at.session_state.agent_answer = "Found some news"
    
    # Trigger the Clear Search button
    # It is located in the sidebar
    assert at.sidebar.button[0].label == "Clear Search"
    at.sidebar.button[0].click().run()
    
    # Assert states were cleared
    assert at.session_state.query == ""
    assert at.session_state.results == []
    assert at.session_state.agent_answer is None
    assert at.session_state.diagnostics is None
    assert at.session_state.agent_markdown is None
