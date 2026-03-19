# PR: V2 Phase 2 - Inference Service (Compute Isolation)

## Description
This PR moves all heavy PyTorch operations (Sentence Transformers & Cross-Encoders) out of the web threads. This guarantees main asynchronous I/O Gateway thread pools are never stalled by Matrix multiplications.

### Changes
* **`inference_service/`**: Micro-FastAPI initialized strictly containing mathematical ML pipelines.
* **Warm Preheating**: Included logic inside the Dockerfile ensuring heavy 1GB models are downloaded dynamically at build-time preventing severe API timeouts during scale-up.
* **`/embed`**: Hosts the `all-MiniLM-L6-v2` dense vector generator.
* **`/rerank`**: Utilizes `ms-marco-MiniLM-L-6-v2` calculating explicit pairwise ranking confidence metrics.

## Testing Instructions
1. Invoke the inference service using `PYTHONPATH=. pytest tests/test_inference.py`.
2. Inspect `docker logs inference_service` to confirm Fastapi initialized securely on `port 8001`.
