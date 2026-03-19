# Comprehensive Development Guide (V2 Architecture)

This document contains the complete technical specifications, architectural diagrams, operational runbooks, and development assumptions for the Enterprise B2B Search engine dynamically scaling locally.

---

## 1. Technical Assumptions & Constraints

To successfully run this robust engine locally, the following architectural shortcuts and constraints were enacted based on the system spec:

1. **System Memory Constraint**:
   To prevent Out-Of-Memory (OOM) failures while running simultaneously with OpenSearch and Machine Learning inference, OpenSearch is capped within `docker-compose.yml` to strict 512mb/1GB thresholds using JVM `-Xms` and `-Xmx` variables.
2. **Library Versions**:
   In order to allow PyTorch to execute `sentence-transformers` inference locally across multiple processor architectures, the environment requires strict usage of `numpy<2.0.0` and `transformers<4.39` to avoid binary incompatibility errors in the open source ecosystem.
3. **Agent Implementation**:
   While production systems would utilize tools like SerpAPI or custom RAG pipelines to find "Recent News", this project implements a mocked static function that uniformly returns a simulated funding insight to demonstrate the autonomous context synthesis pattern without massive API costs.
4. **Data Deduplication**:
   User tagging uses basic `contains()` rules in the Painless script to avoid exact duplicates (case-insensitive string matching logic occurs in the python router boundary).
5. **LLM Pricing Efficiency**:
   We leverage `gemini-3.1-flash-lite-preview` via LiteLLM to maintain blindingly fast intent extraction at the absolute lowest cost, meeting the required scalability of 30 RPS for intelligent parsing tasks.

---

## 2. Repository Structure Overview
```text
project_root/
├── docker-compose.yml       # Orchestration matrix allocating 1.5GB OS Limits
├── Makefile                 # Deterministic local task execution wrapper
├── .env.example             # Defines DNS hostnames pointing to Docker networks natively
├── gateway_api/            
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app/
│       ├── routers/         # search.py (Two-Stage logic), async_tasks.py (Celery delegation), tags.py (Dataset annotation)
│       └── core/            # redis_cache.py (LLM timeout prevention), telemetry.py
├── inference_service/      
│   ├── Dockerfile           # Preheats 1GB .bin matrices actively during build phases
│   ├── requirements.txt
│   ├── app/
│       └── models/          # Thread-safe Singletons for embedding mapping bounds
├── worker/                 
│   ├── Dockerfile
│   └── tasks/
│       └── agent_workflows.py # Deep background polling limits querying GEMINI routines
├── frontend/               
│   ├── Dockerfile
│   └── app.py               # Streamlit application
├── docs/                    # PR specs natively decoupled from Git caches
└── tests/                   # PyTest wrappers bounding gateway logic seamlessly
```

---

## 3. V2 Enterprise Microservices Architecture

The system utilizes an event-driven, decoupled container topology simulating Kubernetes configurations precisely over native local deployments. Compute is strictly isolated from core I/O loops preventing machine learning matrix math from stalling web availability bounds.

### 3.1 Top-Level Container Topology

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
    
    OS[(OpenSearch 2.11<br/>Port 9200)]:::dbLayer
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

### 3.2 Two-Stage Semantic Retrieval Pipeline

The Gateway delegates natural language processing entirely out of the standard Python threads cleanly utilizing robust `cross-encoder` precision boundaries mapping mathematical text overlaps natively.

```mermaid
sequenceDiagram
    participant UI as Streamlit UI
    participant Gateway as Gateway API (8000)
    participant Cache as Redis Cache
    participant LLM as Gemini API
    participant Inf as Inference Service (8001)
    participant OS as OpenSearch (9200)

    UI->>Gateway: POST /api/v2/search/intelligent
    Gateway->>Cache: GET intent:{hash}
    
    alt Cache Miss
        Gateway->>LLM: extract_intent(query)
        LLM-->>Gateway: IntentSchema JSON
        Gateway->>Cache: SETEX intent:{hash}
    end
    
    %% Two Stage
    Gateway->>Inf: POST /embed
    Inf-->>Gateway: 384-d vector (`all-MiniLM-L6-v2`)
    Gateway->>OS: Hybrid Search (Match + KNN)
    OS-->>Gateway: Top 100 Base Candidates
    
    Gateway->>Inf: POST /rerank (Query + 100 Candidates)
    Inf-->>Gateway: Cross-Encoder Scores (`ms-marco-MiniLM-L-6-v2`)
    
    note right of Gateway: Gateway trims payload to Top 10 Results based on Inference Ranking
    
    Gateway-->>UI: Top 10 High Precision Results
```

### 3.3 Asynchronous Agentic Workflows

Deep synthetic LLM tasks parsing heavy news integrations orchestrate smoothly through Redis pub-sub interfaces offloading Celery queues instantly.

```mermaid
sequenceDiagram
    participant UI as Streamlit UI
    participant Gateway as Gateway API
    participant Cache as Redis Cache
    participant Celery as Celery Worker
    participant LLM as Gemini API

    UI->>Gateway: POST /agentic
    Gateway->>Cache: Enqueue Task
    Gateway-->>UI: HTTP 202 (task_id: 123)
    
    loop UI Polling
        UI->>Gateway: GET /tasks/123
        Gateway->>Cache: Check Status
        Cache-->>Gateway: PENDING
        Gateway-->>UI: HTTP 200 (PENDING)
    end
    
    Celery->>Cache: Consume Task 123
    Celery->>LLM: Perform Heavy Synthesis
    LLM-->>Celery: Agentic Final Payload
    Celery->>Cache: Update Status: SUCCESS
    
    UI->>Gateway: GET /tasks/123
    Gateway-->>UI: HTTP 200 (SUCCESS, Result)
```

### 3.4 Telemetry Propagations

Distributed logs propagate uniquely into `Jaeger` tracking traces crossing container lifecycles seamlessly utilizing standard OpenTelemetry Protocol (OTLP).

---

## 4. Setup & Execution Context 

### Initialization
Before engaging local orchestration pipelines natively, you must correctly map the generic network schemas inside the local environment configuration definitions:
```bash
cp .env.example .env
```
Ensure you insert a valid `GEMINI_API_KEY` to guarantee `litellm` routing execution bounds successfully complete operations natively.

### Lifecycle Orchestration
All interactions must stem out from the `Makefile` constraints mapping Docker states. Never run single un-orchestrated python containers utilizing `uvicorn app.main:app` manually, as they will instantly fail binding bounds connecting onto OpenSearch DNS traces natively.
```bash
make build       # Initiates Docker caching heuristics ensuring Inference Torch weights initialize locally
make up          # Silently spans out backend systems onto the Docker hypervisor mapping boundaries
make test        # Validates logic hitting the PyTest assertions
make down        # Gracefully wipes trace footprints terminating execution spans correctly
make ingest      # Executes local python data injections sending chunked requests out tracking embeddings bounding loops directly towards inference bounds natively
```

### Writing Endpoints
Always utilize strict `Pydantic` configurations ensuring payloads mapping into POST bounds guarantee variable limits exactly identically verifying execution sequences globally. Make sure you import the standard `from app.core.telemetry import setup_telemetry` limits inside `main.py` when spinning new isolated nodes.

---

## 5. DevOps & Operational Runbook

This guide covers operational heuristics, debugging matrices, and telemetry tracking schemas required to maintain the V2 microservice footprint accurately.

### 5.1 Tracing Anomalies & Telemetry Operations

`Jaeger` natively intercepts global cross-container HTTP boundary spans exposing execution waterfall paths natively on the local `16686` instance port natively.

**Accessing Distributed Trace Data**:
1. Navigate directly to `http://localhost:16686`
2. Select `Search` natively exploring the local dropdown bounds selecting `gateway_api` or `inference_service` depending precisely on which bounded operation stalled execution metrics natively.
3. Observe exact timestamps representing precisely how computationally expensive the Cross-Encoder `ms-marco-MiniLM` tensor multiplications took executing directly across the local container host OS bounding layers globally.

### 5.2 Asynchronous Queue Inspection & Debugging

If the UI displays perpetual "Loading..." screens endlessly after initiating Intelligent Search queries, the background Celery process is either fatally offline or failed executing the synthetic API payload limits.

**Debugging the Celery Threads**:
Execute strict logging tail commands natively capturing output definitions directly tracking execution failures natively connecting external API keys accurately:
```bash
docker logs celery_worker -f
```
Ensure `litellm` isn't throwing authentication tracebacks or timeout 500 exceptions attempting generating external summaries over the native network layers bounding limits accurately globally.

### 5.3 Storage & Datastore Constraints

OpenSearch instances are aggressively throttled natively via `docker-compose.yml` defining strict JVM limits capping out maximum executions at `-Xmx1024m` globally.

**Recovering OOM Bounds**:
If `docker ps` outlines `opensearch` natively executing internal exit codes `137` identifying Out-Of-Memory limitations natively triggered globally:
1. Increase container limits modifying the native YAML bound footprints assigning `2048M` natively instead precisely tracking operations gracefully natively globally:
   ```yaml
   deploy:
     resources:
       limits:
         memory: 2048M
   ```
2. Restart configurations utilizing `make down` -> `make up` resetting standard JVM footprints accurately across the entire architecture.
