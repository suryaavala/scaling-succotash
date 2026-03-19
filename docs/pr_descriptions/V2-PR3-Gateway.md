# PR: V2 Phase 3 - Gateway Core & Distributed Tracing

## Description
This PR maps exactly over to our primary entrypoint `gateway_api` exposing deterministic endpoints utilizing inter-service communication over TCP to interact heavily with OpenSearch and Inference concurrently.

### Changes
* **Tracing (`gateway_api/app/core/telemetry.py`)**: Bootstrapped `opentelemetry` instrumenting spans targeting the local `jaeger` deployment mapped to HTTP boundaries.
* **Two-Stage Retrieval (`app/services/opensearch_client.py`)**: Migrated queries utilizing remote HTTP embedding retrievals bridging OpenSearch hitting Top 100 loose bounds mathematically refined exactly by Remote NLP Re-Ranker HTTP limits down to Top 10 guarantees.

## Testing Instructions
1. Call tests via `pytest tests/test_gateway.py`. Validate the OpenSearch payload mock assertions hit inference networks.
2. Execute `make test` asserting all boundaries execute successfully natively locally.
