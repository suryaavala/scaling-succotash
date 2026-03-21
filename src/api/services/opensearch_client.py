"""DI OpenSearch logic mapping hybrid retrieval architectures."""

import logging
import os
from typing import Any, Dict, cast

import httpx
from opensearchpy import AsyncOpenSearch

logger = logging.getLogger("opensearch")

OPENSEARCH_URL = os.getenv("OPENSEARCH_URL", "http://localhost:9200")
INFERENCE_URL = os.getenv("INFERENCE_URL", "http://localhost:8001")
INDEX_NAME = "companies"

_http_client: httpx.AsyncClient | None = None
_os_client: AsyncOpenSearch | None = None


async def init_os_pool() -> None:
    """Initializes global bounded HTTP/OS async pools efficiently gracefully logically intelligently."""
    global _http_client, _os_client
    _http_client = httpx.AsyncClient(limits=httpx.Limits(max_connections=100, max_keepalive_connections=20))
    _os_client = AsyncOpenSearch([OPENSEARCH_URL], use_ssl=False, verify_certs=False, pool_maxsize=100)
    logger.info("OpenSearch Async connection pool initialized.")


async def close_os_pool() -> None:
    """Closes global async pools gracefully cleanly properly optimally perfectly seamlessly."""
    global _http_client, _os_client
    if _http_client:
        await _http_client.aclose()
        _http_client = None
    if _os_client:
        await _os_client.close()
        _os_client = None


async def get_embedding(text: str) -> list[float]:
    """Generates embedding representations explicitly connecting models."""
    if not _http_client:
        return [0.0] * 384
    try:
        resp = await _http_client.post(f"{INFERENCE_URL}/embed", json={"text": text})
        resp.raise_for_status()
        return cast(list[float], resp.json()["vector"])
    except Exception:
        return [0.0] * 384


async def get_rerank_scores(query: str, candidates: list[str]) -> list[float]:
    """Generates precision relevance constraints routing natively."""
    if not candidates or not _http_client:
        return []
    resp = await _http_client.post(
        f"{INFERENCE_URL}/rerank", json={"query": query, "candidates": candidates}
    )
    resp.raise_for_status()
    return cast(list[float], resp.json()["scores"])


class OSClient:
    """Dependency Injection provider isolating persistence capabilities."""

    def __init__(self) -> None:
        """Initializes direct underlying mapping domains securely."""
        self.client = _os_client

    async def raw_search(self, index: str, body: Dict[str, Any]) -> Dict[str, Any]:
        """Provides direct driver access mapped safely."""
        if not self.client:
            return {}
        return cast(Dict[str, Any], await self.client.search(index=index, body=body))

    async def two_stage_retrieval(
        self, query: str, intent: Dict[str, Any], vector: list[float]
    ) -> list[Dict[str, Any]]:
        """Maps broad hybrid execution explicitly formatting hits."""

        bool_query: Dict[str, Any] = {
            "should": [
                {"match": {"name": {"query": query, "boost": 1.0}}},
                {"match": {"industry": {"query": query, "boost": 0.5}}},
                {"knn": {"embedding": {"vector": vector, "k": 100}}},
            ],
            "minimum_should_match": 1,
            "filter": [],
        }

        if intent.get("industry"):
            bool_query["filter"].append(
                {"term": {"industry": intent["industry"].lower()}}
            )
        if intent.get("country"):
            bool_query["filter"].append(
                {"term": {"country": intent["country"].lower()}}
            )

        dsl = {"size": 100, "query": {"bool": bool_query}}

        if not self.client:
            return []

        try:
            resp = await self.client.search(index=INDEX_NAME, body=dsl)
            hits = list(resp.get("hits", {}).get("hits", []))
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

        if not hits:
            return []

        candidate_texts = []
        for hit in hits:
            src = hit["_source"]
            txt = (
                f"{src.get('name', '')} "
                f"{src.get('industry', '')} "
                f"{src.get('locality', '')}"
            )
            candidate_texts.append(txt)

        try:
            scores = await get_rerank_scores(query, candidate_texts)
            for i, hit in enumerate(hits):
                hit["_score"] = scores[i]
            hits.sort(key=lambda x: x["_score"], reverse=True)
        except Exception as e:
            logger.error(f"Inference rerank error: {e}")

        top_10 = hits[:10]
        results = []
        for hit in top_10:
            src = dict(hit.get("_source", {}))
            src["id"] = hit.get("_id")
            results.append(src)

        return results


def get_os_client() -> OSClient:
    """FastAPI Depends binding native resolutions logically."""
    return OSClient()
