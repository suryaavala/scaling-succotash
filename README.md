# Enterprise B2B Company Search & Intelligence API (V4 Architecture) 

[![CI/CD Pipeline](https://github.com/suryaavala/scaling-succotash/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/suryaavala/scaling-succotash/actions/workflows/ci.yml)

## Overview
This repository contains a production-grade, distributed microservices architecture for B2B company search. The V4 architecture strictly isolates CPU-heavy ML inference and asynchronous LLM agent workflows from the I/O-bound Web API gateway, ensuring high availability and horizontal scalability. It natively enforces SOLID principles via Dependency Injection and Strategy patterns, while leveraging `uv` for next-generation Python tooling and a standardized `src/` directory layout for robust maintainability.

## Architecture Stack
- **Gateway API**: High-throughput FastAPI handling web routing and orchestration.
- **Inference Service**: Isolated PyTorch container running `SentenceTransformers` and Cross-Encoder ranking.
- **Asynchronous Workers**: Celery + Redis for deep agentic LLM synthesis jobs.
- **Datastore**: OpenSearch 2.11 (capped intelligently to 1GB RAM natively).
- **Intelligence**: LiteLLM (Gemini 3.1 Flash Lite) parsed through strict Pydantic JSON enforcement. Protected actively by `@circuit` resilience bypassing upstream stalls.
- **Caching**: Semantic intent caching mapping raw user questions to bypass LLM timeouts.
- **Observability**: OpenTelemetry distributed tracing exported to a native Jaeger instance.
- **Tooling (V4)**: `uv` for dependency management, `ruff` for linting, and `mypy` for strict typing inside a native `src/` layout.

## V4 Directory Layout
```text
project_root/
├── .github/workflows/ci.yml
├── docker-compose.yml
├── Makefile
├── pyproject.toml
├── README.md
├── GUIDE.md
├── FUTURE.md
├── src/
│   ├── api/            # Gateway Web Target
│   ├── inference/      # ML Target (PyTorch)
│   ├── worker/         # Celery Synthesizer
│   ├── frontend/       # Streamlit UI
│   └── scripts/        # Data Ops
└── tests/
```

## Setup & Running Locally

### Option 1: Kubernetes (V10 Recommended)
We use `kind` (Kubernetes in Docker) for production-parity local orchestration.
**Prerequisites:** Install `kind`, `kubectl`, and `k9s`.

1. **Environment Setup:** `cp .env.example .env` and add `GEMINI_API_KEY`.
2. **Provision Cluster:**
   ```bash
   make cluster-up
   ```
3. **Build & Deploy Workloads:**
   ```bash
   make docker-build-local
   make deploy
   ```
4. **Access the Cluster Natively:**
   Thanks to `kind-config.yaml` host mapping with NodePorts, you can immediately access all services on `localhost` exactly as if you were running Docker Compose (no `kubectl port-forward` needed!).

### Option 2: Docker Compose (Legacy)
1. **Environment Setup:** `cp .env.example .env` and add `GEMINI_API_KEY`.
2. **Deploy:**
   ```bash
   make up
   ```

3. **Automated Dataset Acquisition**
   Download the official Kaggle 7M row dataset (`~/.kaggle/kaggle.json` required):
   ```bash
   make download-data
   ```
   **Fallback:** Generate a 100k-row synthetic mock dataset if Kaggle is unavailable:
   ```bash
   make generate-data
   ```

4. **Containerized Ingestion**
   Execute the isolated Docker ingestion profiles to stream data into the cluster safely:
   ```bash
   make ingest-sample  # Streams 100k generated mock rows
   # OR
   make ingest-full    # Streams the full 7M official Kaggle rows
   ```

5. **Testing & Observability**
   Execute the native E2E test suite against the live cluster to verify Gateway/Inference/Celery bindings:
   ```bash
   uv run pytest -m e2e -v
   ```

6. **Verify Systems**
   - Streamlit Dashboard: `http://localhost:8501`
   - Gateway OpenAPI Docs: `http://localhost:8000/docs`
   - Inference OpenAPI Docs: `http://localhost:8001/docs`
   - Jaeger Tracing UI: `http://localhost:16686`
   - Opensearch Dashboard UI: `http://localhost:5601`

## Documentation
- `docs/architecture.md`: Detailed distributed workflows and Mermaid diagrams.
- `docs/DEVELOPMENT.md`: Codebase mapping and development etiquette.
