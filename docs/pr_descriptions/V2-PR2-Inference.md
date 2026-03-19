# PR: V2 Phase 2 - Inference Service (Compute Isolation)

## Description
This PR moves all heavy PyTorch operations (Sentence Transformers & Cross-Encoders) out of the web threads. This guarantees main asynchronous I/O Gateway thread pools are never stalled by Matrix multiplications.

### Changes Made

1. **Machine Learning API (`inference_service/app/main.py`)**:
   - Initialized a micro-FastAPI container strictly containing mathematical ML pipelines.
   - Exposed `POST /embed` generating `all-MiniLM-L6-v2` dense vectors.
   - Exposed `POST /rerank` utilizing `ms-marco-MiniLM-L-6-v2` calculating explicit pairwise ranking confidence metrics.
2. **Memory Singletons (`inference_service/app/models/`)**:
   - Extracted model initialization into thread-safe singleton patterns.
3. **Build-Time Preheat (`inference_service/Dockerfile`)**:
   - Included logic ensuring 1GB tensor models are downloaded dynamically at build-time preventing severe API timeouts during horizontal scale-up pods.

### Sequence Diagram

```mermaid
sequenceDiagram
    participant Caller as HTTP Client
    participant API as Inference FastAPI
    participant Embed as all-MiniLM-L6-v2
    participant Rank as ms-marco-MiniLM

    Caller->>API: POST /embed {"text": "Company A"}
    API->>Embed: encode("Company A")
    Embed-->>API: [0.12, -0.45, ...]
    API-->>Caller: {"vector": [...]}
    
    Caller->>API: POST /rerank {"query": "AI", "candidates": [...]}
    API->>Rank: predict([[query, doc1], [query, doc2]])
    Rank-->>API: [0.85, 0.12]
    API-->>Caller: {"scores": [...]}
```

## Testing Instructions
1. Invoke the inference service using `PYTHONPATH=. pytest tests/test_inference.py`.
2. Inspect `docker logs inference_service` to confirm Fastapi initialized securely on `port 8001` and loaded `.bin` tensor weights during boot sequence.
