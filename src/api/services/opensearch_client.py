"""OpenSearch implementation of the CompanyRepository interface."""

import logging
from typing import Any, Dict, List, cast

import httpx
from circuitbreaker import CircuitBreakerError, circuit
from opensearchpy import AsyncOpenSearch
from opensearchpy.exceptions import NotFoundError

from src.api.core.config import Settings, get_settings
from src.api.domain.interfaces import CompanyRepository

logger = logging.getLogger("opensearch")

_http_client: httpx.AsyncClient | None = None
_os_client: AsyncOpenSearch | None = None


async def init_os_pool() -> None:
    """Initialize global bounded HTTP/OS async connection pools."""
    global _http_client, _os_client
    settings = get_settings()
    _http_client = httpx.AsyncClient(limits=httpx.Limits(max_connections=100, max_keepalive_connections=20))
    _os_client = AsyncOpenSearch([settings.opensearch_url], use_ssl=False, verify_certs=False, pool_maxsize=100)
    logger.info("OpenSearch async connection pool initialized.")


async def close_os_pool() -> None:
    """Close global async pools gracefully."""
    global _http_client, _os_client
    if _http_client:
        await _http_client.aclose()
        _http_client = None
    if _os_client:
        await _os_client.close()
        _os_client = None


@circuit(failure_threshold=5, recovery_timeout=30)  # type: ignore
async def _fetch_embedding_raw(text: str) -> list[float]:
    settings = get_settings()
    if not _http_client:
        raise RuntimeError("HTTP client not initialized")
    resp = await _http_client.post(f"{settings.inference_url}/embed", json={"text": text})
    resp.raise_for_status()
    return cast(list[float], resp.json()["vector"])


async def get_embedding(text: str) -> list[float]:
    """Generate embedding via the inference service gracefully."""
    try:
        res = await _fetch_embedding_raw(text)
        return cast(list[float], res)
    except CircuitBreakerError:
        logger.error("Circuit breaker OPEN for embedding service. Returning zero vector.")
        return [0.0] * 384
    except Exception as e:
        logger.error(f"Embedding generic error: {e}")
        return [0.0] * 384


@circuit(failure_threshold=5, recovery_timeout=30)  # type: ignore
async def _fetch_rerank_raw(query: str, candidates: list[str]) -> list[float]:
    settings = get_settings()
    if not candidates or not _http_client:
        raise RuntimeError("Invalid candidates or uninitialized HTTP client")
    resp = await _http_client.post(
        f"{settings.inference_url}/rerank",
        json={"query": query, "documents": candidates},
    )
    resp.raise_for_status()
    return cast(list[float], resp.json()["scores"])


async def get_rerank_scores(query: str, candidates: list[str]) -> list[float]:
    """Generate reranking scores via the inference service gracefully."""
    try:
        res = await _fetch_rerank_raw(query, candidates)
        return cast(list[float], res)
    except CircuitBreakerError:
        logger.error("Circuit breaker OPEN for rerank service. Returning zeroed scores.")
        return [0.0] * len(candidates)
    except Exception as e:
        logger.error(f"Reranking generic error: {e}")
        return [0.0] * len(candidates)


class OpenSearchCompanyRepository(CompanyRepository):
    """Concrete CompanyRepository backed by OpenSearch."""

    def __init__(self, settings: Settings | None = None) -> None:
        """Initialize with the global OpenSearch client."""
        self._settings = settings or get_settings()
        self.client = _os_client
        self._index = self._settings.opensearch_index

    async def search(self, query_dsl: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute a raw DSL search and return source documents with IDs."""
        if not self.client:
            return []
        try:
            resp = await self.client.search(index=self._index, body=query_dsl)
            hits = list(resp.get("hits", {}).get("hits", []))
            results = []
            for hit in hits:
                src = hit["_source"]
                src["id"] = hit["_id"]
                results.append(src)
            return results
        except Exception as e:
            logger.error(f"Deterministic search failed: {e}")
            return []

    async def two_stage_retrieval(
        self, query: str, intent: Dict[str, Any], vector: list[float]
    ) -> List[Dict[str, Any]]:
        """Hybrid kNN + text retrieval with reranking."""
        bool_query: Dict[str, Any] = {
            "should": [
                {"match": {"name": {"query": query, "boost": 1.0}}},
                {"match": {"industry": {"query": query, "boost": 0.5}}},
                {"knn": {"embedding": {"vector": vector, "k": 100}}},
            ],
            "minimum_should_match": 1,
        }

        # Use LLM-extracted intent as soft boosts, not hard filters,
        # to avoid zero results when the LLM extracts a non-exact term.
        if intent.get("industry"):
            bool_query["should"].append({"match": {"industry": {"query": intent["industry"].lower(), "boost": 2.0}}})
        if intent.get("country"):
            bool_query["should"].append({"match": {"country": {"query": intent["country"].lower(), "boost": 2.0}}})

        dsl = {"size": 100, "query": {"bool": bool_query}}

        if not self.client:
            return []

        try:
            resp = await self.client.search(index=self._index, body=dsl)
            hits = list(resp.get("hits", {}).get("hits", []))
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

        if not hits:
            return []

        candidate_texts = []
        for hit in hits:
            src = hit["_source"]
            txt = f"{src.get('name', '')} {src.get('industry', '')} {src.get('locality', '')}"
            candidate_texts.append(txt)

        try:
            scores = await get_rerank_scores(query, candidate_texts)
            for i, hit in enumerate(hits):
                hit["_os_score"] = hit.get("_score")
                hit["_score"] = scores[i]
            hits.sort(key=lambda x: x["_score"], reverse=True)
        except Exception as e:
            logger.error(f"Inference rerank error: {e}")

        top_10 = hits[:10]
        results = []
        for hit in top_10:
            src = dict(hit.get("_source", {}))
            src["id"] = hit.get("_id")
            src["re_rank_score"] = hit.get("_score")
            src["knn_score"] = hit.get("_os_score")
            results.append(src)

        return results

    async def add_tag(self, company_id: str, tag: str) -> Dict[str, str]:
        """Add a tag to a company document via painless script."""
        assert self.client is not None, "OpenSearch client is not initialized"
        script = {
            "script": {
                "source": """
                if (ctx._source.tags == null) {
                    ctx._source.tags = new ArrayList();
                }
                if (!ctx._source.tags.contains(params.tag)) {
                    ctx._source.tags.add(params.tag);
                }
                """,
                "lang": "painless",
                "params": {"tag": tag},
            }
        }
        await self.client.update(index=self._index, id=company_id, body=script, refresh=True)
        return {"status": "success", "tag": tag, "company_id": company_id}

    async def get_all_tags(self) -> List[str]:
        """Retrieve all unique tags across the index."""
        assert self.client is not None, "OpenSearch client is not initialized"
        agg_query = {
            "size": 0,
            "aggs": {"unique_tags": {"terms": {"field": "tags.keyword", "size": 1000}}},
        }
        try:
            response = await self.client.search(index=self._index, body=agg_query)
        except NotFoundError:
            return []
        if response.get("hits", {}).get("total", {}).get("value", 0) > 0:
            aggs = response.get("aggregations", {})
            tags_agg = aggs.get("unique_tags", {})
            return [bucket["key"] for bucket in tags_agg.get("buckets", [])]
        return []


# Legacy aliases for backward compatibility
OSClient = OpenSearchCompanyRepository
INDEX_NAME = "companies"


def get_os_client() -> OpenSearchCompanyRepository:
    """FastAPI Depends provider for the CompanyRepository."""
    return OpenSearchCompanyRepository()


def get_company_repository() -> CompanyRepository:
    """FastAPI Depends provider returning the abstract interface."""
    return OpenSearchCompanyRepository()
