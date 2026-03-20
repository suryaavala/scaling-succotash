# Enterprise B2B Company Search (V4 Architecture)

## 1. High-Level Distributed Architecture

The system utilizes a production-grade, distributed microservices architecture (V4) designed for high availability and strict compute isolation. It decouples the Streamlit frontend from the FastAPI routing logic, delegating query execution dynamically via **Dependency Injection** and **Strategy Patterns** (`SemanticSearchStrategy`, `AgenticSearchStrategy`). Machine Learning execution is strictly isolated into an unblockable inference thread.

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
    
    OS[(Datastore: OpenSearch 2.11<br/>Port 9200)]:::dbLayer
    Redis[(Semantic Cache & Broker<br/>Redis)]:::dbLayer
    Jaeger[[Jaeger Tracing<br/>Port 16686]]:::dbLayer

    %% Traces
    Gateway -.->|OTLP Traces| Jaeger
    Inference -.->|OTLP Traces| Jaeger
    
    %% Flows
    UI -->|HTTP REST/JSON| Gateway
    Gateway -->|Semantic Intent Cache| Redis
    
    %% Deterministic & Metadata
    Gateway -->|Tag Management & DSL Queries| OS
    
    %% Two Stage Retrieval
    Gateway -->|POST /embed| Inference
    Gateway -->|Vector Search & Hybrid Search| OS
    Gateway -->|POST /rerank| Inference
    
    %% Async Flow
    Gateway -->|Drop Agent Task| Redis
    Redis -->|Task Queue| Celery
    Celery -->|Write Synthesis Context| Redis
    Celery -->|Intent Extraction & Synthesis| LLM[LLM: Gemini 3.1 Flash Lite]
    Gateway -->|Intent Extraction| LLM
```

**Architecture Components & Data Flow (Mapped to `src/` Layout):**

*   **Frontend UI (`src/frontend/`)**: Built with Streamlit, providing deterministic input fields alongside a conversational chat box for natural language queries. It interacts dynamically with the Gateway via REST API calls.
*   **Gateway API (`src/api/`)**: The highly concurrent FastAPI entry point that routes requests using Dependency Injection. It handles deterministic queries (translating exact payloads into OpenSearch boolean DSL) and intelligent hybrid search (identifying user intent via LiteLLM).
*   **Datastore (OpenSearch 2.11)**: Acts as both an inverted index for keyword matching (BM25) and a vector database utilizing HNSW graphs for semantic cosine similarity. It operates under strict JVM memory caps (512MB to 1GB) to ensure stable local performance.
*   **Inference Service (`src/inference/`)**: A dedicated PyTorch+FastAPI container isolating CPU-bound ML matrix math. It generates 384-dimensional dense vectors via `all-MiniLM-L6-v2` natively at the edge, and executes a massive cross-encoder (`ms-marco-MiniLM-L-6-v2`) for pairwise re-ranking.
*   **Asynchronous Workers (`src/worker/`)**: Deep synthetic LLM tasks parsing heavy news integrations orchestrate smoothly through Redis pub-sub interfaces offloading Celery queues instantly.
*   **Intelligence Layer**: Powered by LiteLLM bound strictly to `gemini-3.1-flash-lite-preview`. It leverages strict Pydantic JSON enforcement to completely prevent conversational hallucinations and extract precise filtering schemas.
*   **Observability**: Standard OpenTelemetry (OTLP) headers are securely injected across the HTTP boundary natively into a Jaeger instance. Developers can visually dissect precise execution lengths traversing from the FastAPI Gateway directly into the Inference service on localhost:16686.

## 2. Two-Stage Retrieval Flow (`/api/v2/search/intelligent`)

*   **Intent Extraction & Semantic Caching**: The gateway hashes the user query to check the Redis semantic cache, preventing expensive repetitive generation costs. If a cache miss occurs, the LLM extracts the search intent into structured JSON using Pydantic.
*   **Stage 1 (High Recall)**: The Gateway calls the Inference Service to embed the query into a dense vector, then executes a broad k-NN hybrid bounds search inside OpenSearch to retrieve the Top 100 loose candidate companies.
*   **Stage 2 (High Precision)**: Exactly these 100 text overlaps are sent to the Remote NLP Re-Ranker endpoint (Cross-Encoder) explicitly scoring pairs. This whittles the candidates down to the Top 10, returning incredibly precise mappings globally.

```mermaid
sequenceDiagram
    participant UI as Streamlit UI
    participant Gateway as Gateway API (src/api)
    participant Cache as Redis Cache
    participant LLM as Gemini API
    participant Inf as Inference Service (src/inference)
    participant OS as OpenSearch

    UI->>Gateway: POST /api/v2/search/intelligent
    Gateway->>Cache: GET intent:{hash}
    
    alt Cache Miss
        Gateway->>LLM: extract_intent(query)
        LLM-->>Gateway: IntentSchema JSON
        Gateway->>Cache: SETEX intent:{hash}
    end
    
    %% Two Stage
    Gateway->>Inf: POST /embed
    Inf-->>Gateway: 384-d vector
    Gateway->>OS: Hybrid Search (Match + KNN)
    OS-->>Gateway: Top 100 Base Candidates
    
    Gateway->>Inf: POST /rerank (Query + 100 Candidates)
    Inf-->>Gateway: Cross-Encoder Scores
    
    note right of Gateway: Gateway trims payload to Top 10 Results based on Inference Ranking
    
    Gateway-->>UI: Top 10 High Precision Results
```

## 3. Asynchronous Agentic Flow (`POST /api/v2/search/agentic`)

Deep agentic tasks (like contextual competitive synthesis or fetching recent funding news) natively bypass standard thread execution to prevent an immediate HTTP stall:
1.  **Queue Deferral**: The Gateway intercepts an agentic requirement and drops the context into a Redis semantic task queue, immediately returning an HTTP 202 `task_id`.
2.  **Background Processing**: The background Celery worker autonomously evaluates the task, calls the simulated Mock API (`search_recent_news`), and triggers the LLM to write a summarized agentic response decoupling totally from Gateway constraints.
3.  **UI Polling**: The Streamlit frontend utilizes an async polling API checking the Celery status execution flags seamlessly without stalling interfaces using HTTP 202 Accepted.

```mermaid
sequenceDiagram
    participant UI as Streamlit UI
    participant Gateway as Gateway API (src/api)
    participant Redis as Redis Broker
    participant Celery as Celery Worker (src/worker)
    participant LLM as Gemini API

    UI->>Gateway: POST /agentic
    Gateway->>Redis: Enqueue Task (synthesize_agent_response)
    Gateway-->>UI: HTTP 202 Accepted (task_id)
    
    loop UI Polling
        UI->>Gateway: GET /tasks/{task_id}
        Gateway->>Redis: Check Status
        Redis-->>Gateway: Status: PENDING
        Gateway-->>UI: HTTP 200 (PENDING)
    end
    
    Celery->>Redis: Consume Task
    Celery->>Celery: Run simulated external News Logic
    Celery->>LLM: Pass Context strings for summarization
    LLM-->>Celery: Agentic Final Payload
    Celery->>Redis: Update Status: SUCCESS (Result)
    
    UI->>Gateway: GET /tasks/{task_id}
    Gateway->>Redis: Check Status
    Redis-->>Gateway: Status: SUCCESS (Result)
    Gateway-->>UI: HTTP 200 (SUCCESS, Result payload)
```
