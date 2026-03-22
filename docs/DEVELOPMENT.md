# Development Guide

This document covers the development workflow, project structure, testing, and architectural patterns for the Enterprise B2B Company Search platform.

---

## 1. Technical Assumptions & Constraints

1. **System Memory**: OpenSearch is capped to 512MB–1024MB JVM heap via `docker-compose.yml` to coexist with ML inference on developer machines.
2. **ML Library Pinning**: `numpy<2.0.0` and `transformers<4.39` are required for PyTorch/sentence-transformers binary compatibility.
3. **Agent Implementation**: The `search_recent_news()` function returns simulated funding insights — production would use SerpAPI or a RAG pipeline.
4. **LLM Provider**: `gemini-3.1-flash-lite-preview` via LiteLLM for fast, low-cost intent extraction.

---

## 2. Repository Structure

```text
project_root/
├── pyproject.toml           # Dependencies, build config, pytest settings
├── uv.lock                  # Deterministic lockfile
├── docker-compose.yml       # Service orchestration
├── Makefile                 # Build/test/deploy automation
├── .github/workflows/       # CI pipeline (lint + coverage)
├── .pre-commit-config.yaml  # Git hooks (ruff, mypy)
│
├── src/
│   ├── api/                 # Gateway API (FastAPI)
│   │   ├── Dockerfile
│   │   ├── main.py          # App entry, lifespan, DI wiring
│   │   ├── core/
│   │   │   ├── config.py    # pydantic-settings Settings class
│   │   │   ├── redis_cache.py
│   │   │   └── telemetry.py
│   │   ├── domain/
│   │   │   ├── interfaces.py # CompanyRepository ABC
│   │   │   └── __init__.py
│   │   ├── routers/
│   │   │   ├── search.py     # /api/v2/search/* endpoints
│   │   │   ├── tags.py       # /api/v2/tags endpoint
│   │   │   └── async_tasks.py # /api/v2/tasks/* polling
│   │   ├── services/
│   │   │   ├── search_service.py      # SearchService orchestrator
│   │   │   ├── search_strategies.py   # Strategy pattern implementations
│   │   │   ├── opensearch_client.py   # OpenSearchCompanyRepository
│   │   │   └── llm_router.py          # LiteLLM intent extraction
│   │   └── models/
│   │       └── schemas.py             # Pydantic request/response schemas
│   │
│   ├── inference/           # ML Inference Service (PyTorch)
│   │   ├── Dockerfile
│   │   ├── main.py          # FastAPI with model warm-up lifespan
│   │   ├── telemetry.py
│   │   └── models/
│   │       ├── embedding_model.py   # all-MiniLM-L6-v2 singleton
│   │       └── reranker_model.py    # ms-marco-MiniLM-L-6-v2 singleton
│   │
│   ├── worker/              # Celery Background Workers
│   │   ├── Dockerfile
│   │   ├── agent_workflows.py  # Agentic task processing
│   │   └── batch_ingestion.py  # Batch data loading
│   │
│   └── frontend/            # Streamlit UI
│       ├── Dockerfile
│       └── app.py
│
├── tests/
│   ├── test_*.py            # 75 unit tests (94% coverage)
│   └── e2e/
│       ├── test_services.py  # Service health + integration tests
│       └── test_search_flow.py # End-to-end search pipeline tests
│
├── scripts/
│   ├── ingest_data.py       # CSV → OpenSearch bulk ingestion
│   ├── download_dataset.py  # Kaggle dataset downloader
│   └── archive_repo.py      # Repo → markdown archival
│
├── data/                    # Runtime data (gitignored, volume-mounted)
├── docs/                    # Architecture, development, Docker docs
└── spec/                    # Version specs and PR descriptions
```

---

## 3. Architecture Patterns (V8)

### 3.1 Repository Pattern

Data access is abstracted behind the `CompanyRepository` interface:

```python
# src/api/domain/interfaces.py
class CompanyRepository(ABC):
    @abstractmethod
    async def search(self, query: str, filters: dict, ...) -> list[dict]: ...

    @abstractmethod
    async def get_all_tags(self) -> list[str]: ...

    @abstractmethod
    async def vector_search(self, vector: list[float], ...) -> list[dict]: ...
```

The concrete implementation `OpenSearchCompanyRepository` in `src/api/services/opensearch_client.py` handles all OpenSearch-specific query DSL. This decouples business logic from storage — enabling testability with mock repositories.

### 3.2 Strategy Pattern

Search routing is implemented via interchangeable strategy objects:

```python
# src/api/services/search_strategies.py
class DeterministicSearchStrategy:
    """Direct keyword + filter queries → OpenSearch."""

class SemanticSearchStrategy:
    """Two-stage retrieval: embed → KNN search → cross-encoder rerank."""

class AgenticSearchStrategy:
    """LLM intent extraction → semantic search + async agent tasks."""
```

The `SearchService` in `search_service.py` delegates to the appropriate strategy based on the endpoint called. Each strategy is independently testable.

### 3.3 Centralized Configuration

All environment variables are validated at startup via `pydantic-settings`:

```python
# src/api/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    OPENSEARCH_URL: str = "http://localhost:9200"
    REDIS_URL: str = "redis://localhost:6379/0"
    INFERENCE_URL: str = "http://localhost:8001"
    GEMINI_API_KEY: str = ""
    PROFILING_ENABLED: bool = False

@lru_cache
def get_settings() -> Settings:
    return Settings()
```

This replaces scattered `os.getenv()` calls with typed, validated, cached configuration.

### 3.4 FastAPI Lifespan

Modern `lifespan` context manager replaces deprecated `@app.on_event()`:

```python
# src/api/main.py
@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_redis_pool(settings.REDIS_URL)
    yield
    await close_redis_pool()

app = FastAPI(lifespan=lifespan)
```

---

## 4. Setup & Execution

### Prerequisites
- Docker Desktop with ≥6GB RAM allocated
- Python 3.11 (via `.python-version`)
- `uv` package manager

### Quick Start
```bash
# Install dependencies
make install-all          # uv sync --frozen (all deps including dev)

# Start services
make up                   # docker compose up --build -d
make wait                 # Poll until gateway + opensearch are healthy

# Ingest data
make ingest LIMIT=10000   # Load 10K companies for testing

# Run tests
make test-fast            # Unit tests with 85% coverage gate
make test-e2e             # E2E tests (starts services automatically)

# Stop
make down                 # docker compose down
```

### Environment Variables
```bash
cp .env.example .env
# Set GEMINI_API_KEY for agentic search functionality
```

---

## 5. Testing

### Test Structure
- **75 unit tests** covering repositories, strategies, configuration, caching, telemetry
- **15 E2E integration tests** covering service health, search pipelines, agentic flows
- **85% coverage floor** enforced via `pytest-cov`

### Running Tests
```bash
make test-fast            # Unit tests only (no Docker needed)
make test-e2e             # E2E tests (requires running services)
make test                 # Both unit + E2E
```

### Test Configuration (`pyproject.toml`)
```toml
[tool.pytest.ini_options]
pythonpath = ["."]
addopts = "--cov=src --cov-report=term-missing --cov-fail-under=85"
markers = [
    "e2e: end-to-end tests requiring running services",
]
```

### E2E Test Resilience
- Services polled with 20 retries × 5s delay before tests start
- Tests gracefully skip if OpenSearch isn't ready
- `test_intelligent_agentic_flow` skips without `GEMINI_API_KEY`

---

## 6. CI/CD Pipeline

### GitHub Actions (`.github/workflows/ci.yml`)

| Job | What it does | Gate |
|-----|-------------|------|
| **lint** | `ruff format --check` + `mypy` | Zero lint errors |
| **coverage** | `pytest` with coverage | ≥85% coverage |

E2E tests run locally via `make test-e2e` (not in CI due to Docker infrastructure requirements).

### Pre-commit Hooks (`.pre-commit-config.yaml`)
- `ruff` — lint and format
- `mypy` — strict type checking

---

## 7. Makefile Targets

| Target | Command | Description |
|--------|---------|-------------|
| `install` | `uv sync --frozen` | Install core deps |
| `install-all` | `uv sync --frozen --all-extras --dev` | Install all deps |
| `up` | `docker compose up --build -d` | Start services |
| `down` | `docker compose down` | Stop services |
| `wait` | `make up` + poll | Wait for service readiness |
| `build` | `docker compose build` | Build images only |
| `test` | `uv run pytest -v` | All tests |
| `test-fast` | `uv run pytest -m "not e2e" -v` | Unit tests only |
| `test-e2e` | `make wait` + `pytest -m e2e` | E2E tests |
| `lint` | `uv run ruff check` | Lint check |
| `format` | `uv run ruff format --check` | Format check |
| `typecheck` | `uv run mypy src/` | Type check |
| `ingest` | `docker compose --profile ingest up` | Data ingestion |
| `archive` | Run `scripts/archive_repo.py` | Repo → markdown |

---

## 8. Debugging

### Gateway Issues
```bash
docker logs gateway_api -f
```

### Celery Worker (Agentic Tasks)
```bash
docker logs celery_worker -f
# Check for LiteLLM auth errors or timeout exceptions
```

### OpenSearch OOM
If `docker ps` shows OpenSearch exit code `137`:
1. Increase memory in `docker-compose.yml`: `memory: 2048M`
2. Restart: `make down && make up`

### Tracing
Visit `http://localhost:16686` (Jaeger UI) to inspect cross-service request traces.
