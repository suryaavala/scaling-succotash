# Enterprise B2B Company Search Architecture (V8)

## 1. System Architecture

The system uses a distributed microservices architecture with strict compute isolation: ML inference is separated from API routing, and long-running LLM tasks are offloaded to background workers via Celery.

```mermaid
graph TD
    classDef frontend fill:#f9f9f9,stroke:#333,stroke-width:2px;
    classDef apiLayer fill:#e1f5fe,stroke:#0288d1,stroke-width:2px;
    classDef worker fill:#fff3e0,stroke:#f57c00,stroke-width:2px;
    classDef ml fill:#fce4ec,stroke:#c2185b,stroke-width:2px;
    classDef dbLayer fill:#e8f5e9,stroke:#388e3c,stroke-width:2px;

    UI([Frontend: Streamlit<br/>Port 8501]):::frontend
    Gateway(Gateway API<br/>FastAPI: src/api):::apiLayer
    Inference(Inference Service<br/>PyTorch: src/inference):::ml
    Celery(Async Workers<br/>Celery: src/worker):::worker

    OS[(OpenSearch 2.11<br/>Port 9200)]:::dbLayer
    Redis[(Redis<br/>Cache + Broker)]:::dbLayer
    Jaeger[[Jaeger Tracing<br/>Port 16686]]:::dbLayer

    %% Traces
    Gateway -.->|OTLP| Jaeger
    Inference -.->|OTLP| Jaeger

    %% Flows
    UI -->|HTTP REST| Gateway
    Gateway -->|Intent Cache| Redis

    %% Deterministic & Metadata
    Gateway -->|BM25 + Filters| OS

    %% Two Stage Retrieval
    Gateway -->|POST /embed| Inference
    Gateway -->|KNN + Hybrid| OS
    Gateway -->|POST /rerank| Inference

    %% Async Flow
    Gateway -->|Enqueue Task| Redis
    Redis -->|Task Queue| Celery
    Celery -->|Write Result| Redis
    Celery -->|Synthesis| LLM[Gemini 3.1 Flash Lite]
    Gateway -->|Intent Extraction| LLM
```

---

## 2. Design Patterns

### 2.1 Repository Pattern (Data Access)

All data access is abstracted behind the `CompanyRepository` ABC in `src/api/domain/interfaces.py`:

```mermaid
classDiagram
    class CompanyRepository {
        <<abstract>>
        +search(query, filters, page, size)
        +get_all_tags()
        +vector_search(vector, query, filters)
        +add_tag(company_id, tag)
    }

    class OpenSearchCompanyRepository {
        -client: AsyncOpenSearch
        +search()
        +get_all_tags()
        +vector_search()
        +add_tag()
    }

    CompanyRepository <|-- OpenSearchCompanyRepository
```

**Benefits:**
- Business logic in strategies/services is decoupled from OpenSearch query DSL
- Unit tests use mock repositories — no Docker needed
- Future migration (e.g., to Elasticsearch or PostgreSQL) only requires a new implementation

### 2.2 Strategy Pattern (Search Routing)

Three search strategies implement different retrieval approaches:

```mermaid
classDiagram
    class SearchService {
        -repo: CompanyRepository
        +deterministic_search()
        +semantic_search()
        +agentic_search()
    }

    class DeterministicSearchStrategy {
        +execute(query, filters, page, size)
    }

    class SemanticSearchStrategy {
        +execute(query, filters)
        -embed(query)
        -knn_search(vector)
        -rerank(query, candidates)
    }

    class AgenticSearchStrategy {
        +execute(query, intent)
        -extract_intent(query)
        -semantic_search(intent)
        -enqueue_agent_task()
    }

    SearchService --> DeterministicSearchStrategy
    SearchService --> SemanticSearchStrategy
    SearchService --> AgenticSearchStrategy
```

| Strategy | Endpoint | Pipeline |
|----------|----------|----------|
| Deterministic | `/api/v2/search/deterministic` | Direct BM25 + filters → OpenSearch |
| Semantic | `/api/v2/search/intelligent` | Embed → KNN → Rerank |
| Agentic | `/api/v2/search/agentic` | Intent → Semantic + Background Agent |

### 2.3 Centralized Configuration

`pydantic-settings` validates all environment variables at startup:

```python
class Settings(BaseSettings):
    OPENSEARCH_URL: str = "http://localhost:9200"
    REDIS_URL: str = "redis://localhost:6379/0"
    INFERENCE_URL: str = "http://localhost:8001"
    GEMINI_API_KEY: str = ""
    PROFILING_ENABLED: bool = False
```

Injected via `get_settings()` (cached singleton) — replaces scattered `os.getenv()`.

---

## 3. Two-Stage Semantic Retrieval (`/api/v2/search/intelligent`)

```mermaid
sequenceDiagram
    participant UI as Streamlit UI
    participant Gateway as Gateway API
    participant Cache as Redis Cache
    participant LLM as Gemini API
    participant Inf as Inference Service
    participant OS as OpenSearch

    UI->>Gateway: POST /api/v2/search/intelligent
    Gateway->>Gateway: Fast-Path Heuristic Check

    alt Fast-Path Hit
        Gateway-->>Gateway: Static IntentSchema
    else Normal Execution
        Gateway->>Cache: GET intent:{hash}
        alt Cache Miss
            par Async Execution
                Gateway->>LLM: extract_intent(query)
                Gateway->>Inf: POST /embed
            end
            LLM-->>Gateway: IntentSchema JSON
            Gateway->>Cache: SETEX intent:{hash} (24h TTL)
        end
    end

    Inf-->>Gateway: 384-d vector (all-MiniLM-L6-v2)
    Gateway->>OS: Hybrid Search (BM25 + KNN)
    OS-->>Gateway: Top 100 Candidates

    Gateway->>Inf: POST /rerank (query + 100 docs)
    Inf-->>Gateway: Cross-Encoder Scores (ms-marco-MiniLM-L-6-v2)

    note right of Gateway: Trim to Top 10 by rerank score

    Gateway-->>UI: Top 10 High-Precision Results
```

**Pipeline Steps:**
1. **Fast-Path**: Regex/dictionary match bypasses LLM entirely (~0ms)
2. **Intent + Embed** (parallel): LLM extracts structured intent while inference computes query vector
3. **Stage 1 (High Recall)**: KNN + BM25 hybrid search retrieves 100 loose candidates
4. **Stage 2 (High Precision)**: Cross-encoder rescores all 100 candidates pairwise, returns top 10

---

## 4. Asynchronous Agentic Flow (`POST /api/v2/search/agentic`)

Heavy LLM synthesis is offloaded to Celery workers to prevent HTTP timeouts:

```mermaid
sequenceDiagram
    participant UI as Streamlit UI
    participant Gateway as Gateway API
    participant Redis as Redis Broker
    participant Celery as Celery Worker
    participant LLM as Gemini API

    UI->>Gateway: POST /agentic
    Gateway->>Redis: Enqueue task (synthesize_agent_response)
    Gateway-->>UI: HTTP 202 Accepted (task_id)

    loop UI Polling
        UI->>Gateway: GET /tasks/{task_id}
        Gateway->>Redis: Check Status
        Redis-->>Gateway: PENDING
        Gateway-->>UI: HTTP 200 (PENDING)
    end

    Celery->>Redis: Consume Task
    Celery->>Celery: search_recent_news() simulation
    Celery->>LLM: Synthesis prompt with context
    LLM-->>Celery: Agentic report payload
    Celery->>Redis: Update Status → SUCCESS (result)

    UI->>Gateway: GET /tasks/{task_id}
    Gateway->>Redis: Check Status
    Redis-->>Gateway: SUCCESS + Result
    Gateway-->>UI: HTTP 200 (SUCCESS, payload)
```

---

## 5. Observability

OpenTelemetry spans propagate across service boundaries via OTLP:

| Service | Instrumented |
|---------|-------------|
| Gateway API | FastAPI auto-instrumentation |
| Inference Service | FastAPI auto-instrumentation |
| Jaeger UI | `http://localhost:16686` |

Trace spans show exact latencies for: intent extraction, embedding, KNN search, reranking, and agent synthesis.

---

## 6. Testing Architecture

| Layer | Count | Coverage | Docker Required |
|-------|-------|----------|----------------|
| Unit tests | 75 | 94% | No |
| E2E tests | 15 | — | Yes |
| Coverage floor | — | 85% | Enforced in CI |

Unit tests use mock repositories and strategies — no OpenSearch/Redis needed. E2E tests hit live containers via `make test-e2e`.
