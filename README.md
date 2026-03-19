# Enterprise B2B Company Search API

## Overview
This repository contains a production-grade, highly-available containerized system executing advanced Two-Stage Semantic Retrieval workflows utilizing isolated Machine Learning PyTorch tensor computations and deep autonomous asynchronous Celery workflow handlers reliably mapping natural language searches directly against 7M dynamically injected OpenSearch entity datasets cleanly globally natively accurately.

## Architecture Stack Structure
1. **API Gateway (`gateway_api`)**: Exposes FastAPI endpoints mapping two-stage caching heuristics.
2. **Inference Node (`inference_service`)**: Highly decoupled PyTorch REST boundaries executing embedding encodings globally safely blocking standard HTTP IO bottlenecks natively safely.
3. **Queue Consumers (`worker`)**: Redis pub-sub interfaces bridging Celery daemon tasks handling arbitrary asynchronous API completions mapping logic seamlessly into frontend polling endpoints precisely accurately.
4. **Local Datastores**: Redis (Caching logic mappings safely), OpenSearch (KNN Vector computations utilizing memory isolation caps).
5. **Observability**: OpenTelemetry generating span tracking loops bridging container bounds accurately mapped locally towards Jaeger instances directly natively automatically.

## Local Execution Flow
1. Copy `.env` mapping variables safely locally bounds gracefully:
```bash
cp .env.example .env
```
*(Insert GEMINI API tokens mapping authentication safely)*

2. Spin up the cluster utilizing native `Makefile` orchestrated loops bounding container topologies accurately directly:
```bash
make up
```

3. Ensure system states correctly spanning locally navigating accurately globally bounding endpoints natively explicitly:
- **UI Interaction**: `http://localhost:8501`
- **Tracing Matrix**: `http://localhost:16686`
- **Gateway Swagger**: `http://localhost:8000/docs`

## Documentation & Runbooks
The documentation folder maintains granular matrices mapping code footprints, network diagrams, and operational troubleshooting definitions.
- `docs/architecture.md`: Detailed workflows and sequence diagrams.
- `docs/DEVELOPMENT.md`: System layout spanning boundaries seamlessly safely.
- `docs/RUNBOOK.md`: Troubleshooting logic bounding Redis states, Celery failures and JVM OOM recoveries.
