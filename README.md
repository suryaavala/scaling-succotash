# Enterprise B2B Company Search & Intelligence API (V4 Architecture)

## Overview
This repository contains a production-grade, distributed microservices architecture for B2B company search. The V4 architecture strictly isolates CPU-heavy ML inference and asynchronous LLM agent workflows from the I/O-bound Web API gateway, ensuring high availability and horizontal scalability. It natively enforces SOLID principles via Dependency Injection and Strategy patterns, while leveraging `uv` for next-generation Python tooling and a standardized `src/` directory layout for robust maintainability.

## Architecture Stack
- **Gateway API**: High-throughput FastAPI handling web routing and orchestration.
- **Inference Service**: Isolated PyTorch container running `SentenceTransformers` and Cross-Encoder ranking.
- **Asynchronous Workers**: Celery + Redis for deep agentic LLM synthesis jobs.
- **Datastore**: OpenSearch 2.11 (capped intelligently to 1GB RAM natively).
- **Intelligence**: LiteLLM (Gemini 3.1 Flash Lite) parsed through strict Pydantic JSON enforcement.
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

## Setup & Running Locally (Docker Compose)

1. **Environment Setup**
   Copy the example environment into place:
   ```bash
   cp .env.example .env
   ```
   Add your valid `GEMINI_API_KEY` to `.env`.

2. **Orchestrate via Make**
   Deploy the entire application automatically:
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
