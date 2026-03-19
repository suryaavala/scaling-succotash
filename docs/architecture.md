# Architecture Details

This document outlines the detailed system architecture, codebase breakdown, retrieval pipelines, and sequence flows of the Enterprise Company Search API system. The architecture is deeply coupled to the exact Python codebase implementations throughout the `app/` directory.

## 1. High-Level System Architecture

The system decouples the Streamlit frontend from the FastAPI routing logic, which delegates to specialized service modules depending on whether the query is deterministic or natural language.

```mermaid
graph TD
    %% Node Styles
    classDef frontend fill:#f9f9f9,stroke:#333,stroke-width:2px;
    classDef apiLayer fill:#e1f5fe,stroke:#0288d1,stroke-width:2px;
    classDef svcLayer fill:#fff3e0,stroke:#f57c00,stroke-width:2px;
    classDef modelLayer fill:#fce4ec,stroke:#c2185b,stroke-width:2px;
    classDef dbLayer fill:#e8f5e9,stroke:#388e3c,stroke-width:2px;

    %% Nodes
    UI([Streamlit App<br/>frontend/app.py]):::frontend
    FastAPI(FastAPI App<br/>app/main.py):::apiLayer
    
    %% Routers
    SearchRouter(Search Router<br/>app/api/routers/search.py):::apiLayer
    TagsRouter(Tags Router<br/>app/api/routers/tags.py):::apiLayer

    %% Services
    SearchSvc(Search Service<br/>app/services/search_service.py):::svcLayer
    IntelSvc(Intelligence Service<br/>app/services/intelligence_service.py):::svcLayer
    AgentSvc(Agent Service<br/>app/services/agent_service.py):::svcLayer

    %% Models
    STransformer(SentenceTransformer<br/>'all-MiniLM-L6-v2'):::modelLayer
    Gemini(Gemini Flash Lite<br/>via LiteLLM):::modelLayer
    MockNews{{Mock News Tool<br/>agent_service.py}}:::modelLayer

    %% DB
    OS[(OpenSearch 2.11<br/>index: companies)]:::dbLayer

    %% Connections
    UI -->|HTTP POST| SearchRouter
    UI -->|HTTP POST / GET| TagsRouter
    
    TagsRouter -->|Painless scripts & Aggregations| OS

    %% Standard Path
    SearchRouter -->|POST /api/v1/search| SearchSvc
    SearchSvc -->|build_search_dsl| OS
    
    %% Intelligent Path
    SearchRouter -->|POST /api/v1/search/intelligent| IntelSvc
    IntelSvc -->|"extract_intent(query)"| Gemini
    IntelSvc -->|"encode(query)"| STransformer
    IntelSvc -->|"hybrid_search(intent, vector)"| OS
    
    %% Agentic Path
    SearchRouter -->|requires_agent=True| AgentSvc
    AgentSvc -->|Loop top 5 domains| MockNews
    AgentSvc -->|synthesize_agent_response| Gemini
```

---

## 2. Pydantic Domain Entities

The API strictly governs request/response boundaries via `app/models/schemas.py`:

```mermaid
classDiagram
    direction LR
    
    class Company {
        +String id
        +String name
        +String domain
        +String industry
        +String locality
        +String country
        +String size_range
        +Integer year_founded
        +List~String~ tags
    }

    class SearchRequest {
        +String name
        +String industry
        +String size_range
        +String country
        +Integer year_from
        +Integer year_to
        +Integer page
        +Integer size
    }

    class SearchResponse {
        +Integer total
        +Integer page
        +Integer size
        +List~Company~ results
    }
    
    class IntelligentSearchRequest {
        +String query
    }
    
    class IntelligentSearchResponse {
        +String agentic_answer
        +SearchResponse search_results
    }

    SearchResponse "1" *-- "many" Company : contains
    IntelligentSearchResponse "1" *-- "1" SearchResponse : contains
```

---

## 3. Core Operational Sequences

### 3.1 Deterministic Search Sequence (`POST /api/v1/search`)
Fast, exact-match searches relying entirely on `build_search_dsl` mapped to OpenSearch boolean logic (`must` matches and `term`/`range` filters).

```mermaid
sequenceDiagram
    participant UI as frontend/app.py
    participant API as app/api/routers/search.py
    participant Svc as app/services/search_service.py
    participant OS as OpenSearch (companies index)

    UI->>API: POST /api/v1/search (SearchRequest)
    API->>Svc: build_search_dsl(request)
    note right of Svc: Maps 'name' to 'must -> match'<br/>Maps 'industry' to 'filter -> term'
    Svc-->>API: Dict (OpenSearch DSL)
    API->>OS: client.search(body=dsl)
    OS-->>API: Hits JSON
    API-->>UI: SearchResponse (Validated Pydantic)
```

### 3.2 Intelligent Search & Agentic Fallback Sequence (`POST /api/v1/search/intelligent`)
The intelligent API orchestrates structured response parsing from Gemini, falls back to a custom local-vector hybrid query, and injects context into a secondary generative synthesis loop.

```mermaid
sequenceDiagram
    participant UI as frontend/app.py
    participant Router as routers/search.py
    participant Intel as intelligence_service.py
    participant Gemini as LiteLLM (Gemini)
    participant ST as SentenceTransformer
    participant OS as OpenSearch
    participant Agent as agent_service.py

    UI->>Router: POST /intelligent (query="AI startups in US funding")
    
    %% Intent Extraction
    Router->>Intel: extract_intent(query)
    Intel->>Gemini: Prompt + response_format=IntentSchema
    Gemini-->>Intel: JSON string
    Intel-->>Router: parsed IntentSchema (requires_agent=True, country="us")
    
    %% Vector/Hybrid Fallback
    Router->>Intel: hybrid_search(query, intent)
    Intel->>ST: get_embed_model().encode(query)
    ST-->>Intel: float[] (384-dimensional vector)
    
    note right of Intel: Builds bool query combining:<br/>1. match: name (boost=1.0)<br/>2. match: industry (boost=0.5)<br/>3. knn: embedding (k=20)<br/>4. filter: country="us"
    
    Intel->>OS: search(body=hybrid_dsl)
    OS-->>Intel: Hits JSON
    Intel-->>Router: SearchResponse (Base Candidates)
    
    %% Agentic Branch
    opt requires_agent == True (from IntentSchema)
        Router->>Agent: synthesize_agent_response(query, Base Candidates)
        
        loop For Top 5 Candidates
            Agent->>Agent: search_recent_news(candidate.domain)
            note right of Agent: "Announced $10M Series A funding..."
        end
        
        Agent->>Gemini: Prompt: [User Query] + [Candidate Context + News]
        Gemini-->>Agent: Natural language summary string
        Agent-->>Router: agentic_answer string
    end
    
    Router-->>UI: IntelligentSearchResponse (Results + Agent Answer)
```

---

## 4. Tagging Architecture Sequence (`POST /api/v1/companies/{id}/tags`)
The tagging system is strictly implemented on the backend datastore avoiding inefficient read-modify-write Python blocks.

```mermaid
sequenceDiagram
    participant UI as frontend/app.py
    participant API as tags.py
    participant OS as OpenSearch
    
    UI->>API: POST /api/v1/companies/123/tags {"tag": "competitor"}
    API->>API: Validate tag string
    API->>OS: client.update(id="123", body={script: Painless})
    note right of API: Painless Script logic:<br/>if (tags == null) init List;<br/>if (!tags.contains) add tag;
    OS-->>API: 200 OK (Updated Document)
    API-->>UI: 200 OK
```

---

## 5. Streaming Ingestion Pipeline

To solve the 7 million row out-of-memory bottleneck defined in the specs, ingestion leverages Polars lazy chunking alongside pipelined vectorizations.

```mermaid
flowchart LR
    CSV[(data/companies.csv)] -->|pl.read_csv_batched<br/>batch_size=5000| Loop[While chunk in batches]
    
    subgraph Python Chunking Loop [ingest_data.py]
    Loop --> Clean[Lowercasing & Cast Ints]
    Clean --> StringMerge[concat: name+industry+locality]
    StringMerge -->|Encode| STrans[SentenceTransformers<br/>encode(batch)]
    STrans --> BuildDoc[Build OpenSearch JSON Doc]
    Clean --> BuildDoc
    end
    
    BuildDoc -->|Bulk API actions| OS[(OpenSearch <br/>index: companies)]
    
    OS --> Loop
```
