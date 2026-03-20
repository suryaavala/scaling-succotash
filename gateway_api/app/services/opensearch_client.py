"""DI OpenSearch logic mapping hybrid retrieval architectures."""

import logging
import os
from typing import Any, Dict, cast

import requests
from opensearchpy import OpenSearch

logger = logging.getLogger("opensearch")

OPENSEARCH_URL = os.getenv("OPENSEARCH_URL", "http://localhost:9200")
INFERENCE_URL = os.getenv("INFERENCE_URL", "http://localhost:8001")
INDEX_NAME = "companies"


def get_embedding(text: str) -> list[float]:
    """Generates embedding representations explicitly connecting models."""
    resp = requests.post(f"{INFERENCE_URL}/embed", json={"text": text})
    resp.raise_for_status()
    return cast(list[float], resp.json()["vector"])


def get_rerank_scores(query: str, candidates: list[str]) -> list[float]:
    """Generates precision relevance constraints routing natively."""
    if not candidates:
        return []
    resp = requests.post(
        f"{INFERENCE_URL}/rerank", json={"query": query, "candidates": candidates}
    )
    resp.raise_for_status()
    return cast(list[float], resp.json()["scores"])


class OSClient:
    """Dependency Injection provider isolating persistence capabilities."""

    def __init__(self) -> None:
        """Initializes direct underlying mapping domains securely."""
        self.client = OpenSearch([OPENSEARCH_URL], use_ssl=False, verify_certs=False)

    def raw_search(self, index: str, body: Dict[str, Any]) -> Dict[str, Any]:
        """Provides direct driver access mapped safely."""
        return cast(Dict[str, Any], self.client.search(index=index, body=body))

    def two_stage_retrieval(
        self, query: str, intent: Dict[str, Any]
    ) -> list[Dict[str, Any]]:
        """Maps broad hybrid execution explicitly formatting hits."""
        try:
            vector = get_embedding(query)
        except Exception as e:
            logger.error(f"Inference embed error: {e}")
            vector = [0.0] * 384

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

        try:
            resp = self.client.search(index=INDEX_NAME, body=dsl)
            hits = resp["hits"]["hits"]
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
            scores = get_rerank_scores(query, candidate_texts)
            for i, hit in enumerate(hits):
                hit["_score"] = scores[i]
            hits.sort(key=lambda x: x["_score"], reverse=True)
        except Exception as e:
            logger.error(f"Inference rerank error: {e}")

        top_10 = hits[:10]
        results = []
        for hit in top_10:
            src = hit["_source"]
            src["id"] = hit["_id"]
            results.append(src)

        return results


def get_os_client() -> OSClient:
    """FastAPI Depends binding native resolutions logically."""
    return OSClient()
