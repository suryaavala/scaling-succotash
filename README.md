# Enterprise B2B Company Search & Intelligence API (V3 Architecture)

## Overview
This repository contains a production-grade, distributed microservices architecture for B2B company search. The V3 architecture strictly isolates CPU-heavy ML inference and asynchronous LLM agent workflows from the I/O-bound Web API gateway, ensuring high availability and horizontal scalability. It natively enforces SOLID principles via Dependency Injection and Strategy patterns, while leveraging `uv` for next-generation Python tooling.

## Architecture Stack
- **Gateway API**: High-throughput FastAPI handling web routing and orchestration.
- **Inference Service**: Isolated PyTorch container running `SentenceTransformers` and Cross-Encoder ranking.
- **Asynchronous Workers**: Celery + Redis for deep agentic LLM synthesis jobs.
- **Datastore**: OpenSearch 2.11 (capped intelligently to 1GB RAM natively).
- **Intelligence**: LiteLLM (Gemini 3.1 Flash Lite) parsed through strict Pydantic JSON enforcement.
- **Caching**: Semantic intent caching mapping raw user questions to bypass LLM timeouts.
- **Observability**: OpenTelemetry distributed tracing exported to a native Jaeger instance.
- **Tooling (V3)**: `uv` for dependency management, `ruff` for linting, and `mypy` for strict typing.

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

3. **Ingest Data**
   Stream 7 million rows of `.csv` data effectively via the batching container:
   ```bash
   make ingest
   ```

4. **Verify Systems**
   - Streamlit Dashboard: `http://localhost:8501`
   - Gateway OpenAPI Docs: `http://localhost:8000/docs`
   - Inference OpenAPI Docs: `http://localhost:8001/docs`
   - Jaeger Tracing UI: `http://localhost:16686`

## Documentation
- `docs/architecture.md`: Detailed distributed workflows and Mermaid diagrams.
- `docs/DEVELOPMENT.md`: Codebase mapping and development etiquette.
