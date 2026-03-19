# PR: V2 Phase 1 - Distributed Infrastructure & DevEx

## Description
This PR bridges the gap between local monolithic execution and a true distributed microservice topology. It isolates environments mirroring production Kubernetes clusters but executed seamlessly locally via Compose.

### Changes
* **`docker-compose.yml`**: Defines 7 explicit containers: `gateway_api`, `inference_service`, `celery_worker`, `opensearch`, `redis`, `jaeger`, and `frontend`. Applied strict memory boundaries (`1.5GB` limit for JVM OS layer).
* **`Makefile`**: Bootstraps standardized deterministic scripts (`make up`, `make down`, `make test`).
* **`.env.example`**: Outlines networking URLs mapped to native Docker internal DNS routing schemas.

## Testing Instructions
1. Run `make up`. Observe all 7 containers boot successfully without immediate exit codes.
2. Run `docker stats` ensuring memory caps are strictly enforced on `opensearch`.
