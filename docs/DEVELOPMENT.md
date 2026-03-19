# Development & Etiquette Guide (V2 Architecture)

## Repository Structure (Decoupled Microservices)
```
project_root/
├── docker-compose.yml
├── Makefile
├── .env.example
├── gateway_api/            
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app/
│       ├── main.py
│       ├── routers/      (search.py, tags.py, async_tasks.py)
│       ├── services/     (opensearch_client.py, llm_router.py)
│       └── core/         (redis_cache.py, telemetry.py)
├── inference_service/      
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app/
│       ├── main.py
│       ├── telemetry.py
│       └── models/       (embedding_model.py, reranker_model.py)
├── worker/                 
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── tasks/            (agent_workflows.py, batch_ingestion.py)
├── frontend/               
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app.py
├── docs/                   (pr_descriptions, architecture mappings)
└── tests/
    ├── test_gateway.py
    └── test_inference.py
```

## Orchestrating Operations
Streamlined Docker usage is encapsulated strictly via massive `make` operations. Never spin up isolated single containers without network context guarantees.

```bash
make up         # Boots OS, Redis, Celery, Gateway, Inference, Jaeger, UI
make test       # Executes multi-directional Python PyTest mocks identically
make ingest     # Lazily streams data directly via HTTP to embedding endpoints
```

## Pull Request Strategy Implementation
All features were built sequentially resolving core constraints:
- `PR 1`: Setup localized infrastructure configurations mimicking Kubernetes footprints cleanly.
- `PR 2`: Extracted tight `SentenceTransformers` execution threads preventing FastAPI blocking calls.
- `PR 3`: Designed semantic `Redis` bypassed logic saving identical inference intent LLM loops.
- `PR 4`: Wrapped autonomous synthetic news data explicitly handling HTTP `202 PENDING` codes seamlessly.
