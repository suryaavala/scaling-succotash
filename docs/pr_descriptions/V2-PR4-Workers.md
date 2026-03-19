# PR: V2 Phase 4 - Agentic Asynchronous Task Queues

## Description
This PR stabilizes edge-case extreme latencies originating strictly from autonomous multi-stage LLM generation flows. It bridges FastAPI gateways returning deterministic 202 IDs mapped against Celery background queue processing pipelines.

### Changes Made

1. **Redis Semantic Caching (`gateway_api/app/core/redis_cache.py`)**:
   - Intercepts intelligent LLM intent classification hashing input raw-strings, completely blocking heavy HTTP LiteLLM traffic for previously asked questions over 24-hr expiry windows.
2. **Celery Deep Workers (`worker/tasks/agent_workflows.py`)**:
   - Offloads autonomous LLM document context integrations silently parsing mock news pipelines decoupled totally from Gateway constraints.
3. **Asynchronous Polling APIs (`gateway_api/app/routers/async_tasks.py`)**:
   - Handles Streamlit frontend requests checking Celery status execution flags seamlessly without stalling interfaces using `HTTP 202 Accepted`.

### Sequence Diagram

```mermaid
sequenceDiagram
    participant UI as Streamlit UI
    participant Gateway as Gateway API
    participant Cache as Redis Cache
    participant Celery as Celery Worker
    participant LLM as Gemini API

    UI->>Gateway: POST /agentic
    Gateway->>Cache: SETEX intent:{hash}
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

## Testing Instructions
1. Run application UI natively via Streamlit.
2. Issue an agentic specific natural language query. Watch the UI immediately spin in polling mode while `docker logs celery_worker` outputs synthesis completion queues. 
