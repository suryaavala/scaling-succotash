"""Unit tests for search_service DSL edge cases."""

from src.api.models.schemas import SearchRequest
from src.api.services.search_service import build_search_dsl


def test_build_search_dsl_with_tags() -> None:
    """Test DSL generation with tag filters."""
    req = SearchRequest(tags=["priority", "vip"])
    dsl = build_search_dsl(req)
    filters = dsl["query"]["bool"]["filter"]
    tag_filters = [f for f in filters if "term" in f and "tags" in f["term"]]
    assert len(tag_filters) == 2


def test_build_search_dsl_with_size_range() -> None:
    """Test DSL generation with size_range filter."""
    req = SearchRequest(size_range="51-200")
    dsl = build_search_dsl(req)
    filters = dsl["query"]["bool"]["filter"]
    assert any("term" in f and "size_range" in f["term"] for f in filters)


def test_build_search_dsl_pagination() -> None:
    """Test DSL pagination offset calculation."""
    req = SearchRequest(page=3, size=20)
    dsl = build_search_dsl(req)
    assert dsl["from"] == 40  # (3-1) * 20
    assert dsl["size"] == 20


def test_build_search_dsl_year_from_only() -> None:
    """Test DSL with only year_from."""
    req = SearchRequest(year_from=2000)
    dsl = build_search_dsl(req)
    filters = dsl["query"]["bool"]["filter"]
    range_filter = [f for f in filters if "range" in f and "year_founded" in f["range"]]
    assert len(range_filter) == 1
    assert range_filter[0]["range"]["year_founded"]["gte"] == 2000
    assert "lte" not in range_filter[0]["range"]["year_founded"]


def test_build_search_dsl_year_to_only() -> None:
    """Test DSL with only year_to."""
    req = SearchRequest(year_to=2020)
    dsl = build_search_dsl(req)
    filters = dsl["query"]["bool"]["filter"]
    range_filter = [f for f in filters if "range" in f and "year_founded" in f["range"]]
    assert len(range_filter) == 1
    assert range_filter[0]["range"]["year_founded"]["lte"] == 2020
    assert "gte" not in range_filter[0]["range"]["year_founded"]
