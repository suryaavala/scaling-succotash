"""Module docstring mapped natively."""

from src.api.models.schemas import SearchRequest
from src.api.services.search_service import build_search_dsl


def test_build_search_dsl_empty() -> None:
    """Native test execution mapping bound."""
    req = SearchRequest()
    dsl = build_search_dsl(req)
    assert "match_all" in dsl["query"]


def test_build_search_dsl_filters() -> None:
    """Native test execution mapping bound."""
    req = SearchRequest(
        name="IBM", industry="Technology", country="US", year_from=1900, year_to=2000
    )
    dsl = build_search_dsl(req)

    bool_query = dsl["query"]["bool"]

    musts = bool_query["must"]
    assert any("match" in m and "name" in m["match"] for m in musts)

    filters = bool_query["filter"]
    assert any("term" in f and "industry" in f["term"] for f in filters)
    assert any("term" in f and "country" in f["term"] for f in filters)
    assert any("range" in f and "year_founded" in f["range"] for f in filters)
