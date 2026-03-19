# PR: V2 Phase 4 - Agentic Asynchronous Task Queues

## Description
This PR stabilizes edge-case extreme latencies originating strictly from autonomous multi-stage LLM generation flows. It bridges FastAPI gateways returning deterministic 202 IDs mapped against Celery background queue processing pipelines.

### Changes
* **Redis Caching (`app/core/redis_cache.py`)**: Intercepts intelligent LLM intent classification hashing input raw-strings blocking heavy LLM traffic over 24-hr expiry windows.
* **Celery Workers (`worker/tasks/`)**: Offloads LLM document context integrations silently parsing deep news pipelines decoupled totally from Gateway constraints.
* **Async Polling (`app/routers/async_tasks.py`)**: Handles Streamlit frontend requests checking status execution flags seamlessly without stalling interfaces.

## Testing Instructions
1. Run application UI natively via Streamlit mapped externally mapping to explicit agent triggers targeting background logs monitoring `docker logs celery_worker` outputs seamlessly monitoring completion queues.
