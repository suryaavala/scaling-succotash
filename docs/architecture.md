# V2 Microservices Architecture Details

## 1. High-Level Distributed Architecture

The system decouples the Streamlit frontend from the FastAPI routing logic, which delegates to specialized service modules depending on whether the query is deterministic or natural language. ML execution is strictly isolated into an unblockable inference thread.

```mermaid
graph TD
    classDef frontend fill:#f9f9f9,stroke:#333,stroke-width:2px;
    classDef apiLayer fill:#e1f5fe,stroke:#0288d1,stroke-width:2px;
    classDef worker fill:#fff3e0,stroke:#f57c00,stroke-width:2px;
    classDef ml fill:#fce4ec,stroke:#c2185b,stroke-width:2px;
    classDef dbLayer fill:#e8f5e9,stroke:#388e3c,stroke-width:2px;

    UI([Streamlit App<br/>Port 8501]):::frontend
    Gateway(Gateway API<br/>FastAPI: Port 8000):::apiLayer
    Inference(Inference Service<br/>PyTorch: Port 8001):::ml
    Celery(Celery Worker<br/>agent_workflows):::worker
    
    OS[(OpenSearch 2.x<br/>Port 9200)]:::dbLayer
    Redis[(Redis Cache<br/>Port 6379)]:::dbLayer
    Jaeger[[Jaeger Tracing<br/>Port 16686]]:::dbLayer

    %% Traces
    Gateway -.->|OTel Traces| Jaeger
    Inference -.->|OTel Traces| Jaeger
    
    %% Flows
    UI -->|HTTP POST| Gateway
    Gateway -->|Semantic Intent Cache| Redis
    
    %% Two Stage Retrieval
    Gateway -->|POST /embed| Inference
    Gateway -->|Hybrid Search| OS
    Gateway -->|POST /rerank| Inference
    
    %% Async Flow
    Gateway -->|Drop Task| Redis
    Redis -->|Pick up Job| Celery
    Celery -->|Write Result| Redis
    Celery --> OS
```

## 2. Two-Stage Retrieval Flow (`/api/v2/search/intelligent`)

```mermaid
sequenceDiagram
    participant UI as Streamlit UI
    participant Gateway as Gateway API
    participant Cache as Redis Cache
    participant LLM as Gemini API
    participant Inf as Inference Service
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

```mermaid
sequenceDiagram
    participant UI as Streamlit UI
    participant Gateway as Gateway API
    participant Redis as Redis Broker
    participant Celery as Celery Worker
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
