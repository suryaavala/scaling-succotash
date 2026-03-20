"""Module docstring mapped natively."""
import logging
import os
from typing import List

import requests
from opensearchpy import OpenSearch

logger = logging.getLogger("opensearch")

OPENSEARCH_URL = os.getenv("OPENSEARCH_URL", "http://localhost:9200")
INFERENCE_URL = os.getenv("INFERENCE_URL", "http://localhost:8001")
INDEX_NAME = "companies"

def get_opensearch_client():
    return OpenSearch([OPENSEARCH_URL], use_ssl=False, verify_certs=False)

def get_embedding(text: str) -> list[float]:
    resp = requests.post(f"{INFERENCE_URL}/embed", json={"text": text})
    resp.raise_for_status()
    return resp.json()["vector"]

def get_rerank_scores(query: str, candidates: List[str]) -> list[float]:
    if not candidates: return []
    resp = requests.post(f"{INFERENCE_URL}/rerank", json={
        "query": query,
        "candidates": candidates
    })
    resp.raise_for_status()
    return resp.json()["scores"]

def two_stage_retrieval(query: str, intent: dict) -> list[dict]:
    try:
        vector = get_embedding(query)
    except Exception as e:
        logger.error(f"Inference embed error: {e}")
        vector = [0.0] * 384
        
    client = get_opensearch_client()
    
    # 1. Broad Hybrid Search for Top 100
    bool_query = {
        "should": [
            {"match": {"name": {"query": query, "boost": 1.0}}},
            {"match": {"industry": {"query": query, "boost": 0.5}}},
            {"knn": {"embedding": {"vector": vector, "k": 100}}}
        ],
        "minimum_should_match": 1,
        "filter": []
    }
    
    if intent.get("industry"):
        bool_query["filter"].append({"term": {"industry": intent["industry"].lower()}})
    if intent.get("country"):
        bool_query["filter"].append({"term": {"country": intent["country"].lower()}})
        
    dsl = {
        "size": 100,
        "query": {"bool": bool_query}
    }
    
    try:
        resp = client.search(index=INDEX_NAME, body=dsl)
        hits = resp["hits"]["hits"]
    except Exception as e:
        logger.error(f"Search failed: {e}")
        return []
    
    if not hits:
        return []
        
    # 2. Rerank using Cross-Encoder via remote Inference API boundary
    candidate_texts = []
    for hit in hits:
        src = hit["_source"]
        txt = f"{src.get('name','')} {src.get('industry','')} {src.get('locality','')}"
        candidate_texts.append(txt)
        
    try:
        scores = get_rerank_scores(query, candidate_texts)
        for i, hit in enumerate(hits):
            hit["_score"] = scores[i]
        hits.sort(key=lambda x: x["_score"], reverse=True)
    except Exception as e:
        logger.error(f"Inference rerank error: {e}")
        
    # 3. Return Top 10
    top_10 = hits[:10]
    
    results = []
    for hit in top_10:
        src = hit["_source"]
        src["id"] = hit["_id"]
        results.append(src)
        
    return results
