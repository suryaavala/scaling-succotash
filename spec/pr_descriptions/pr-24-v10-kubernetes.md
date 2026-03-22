# V10: Kubernetes Orchestration & Local DevEx

Transitioning local development orchestration from Docker Compose to Kubernetes using `kind` to ensure production parity.

## Architecture & Infrastructure Updates
- **Lightweight Local K8s**: Added `k8s/kind-config.yaml` to provision a 1-control plane, 2-worker local cluster with NGINX ingress bindings.
- **Kustomize Manifests**: Created declarative Kubernetes YAML definitions under `k8s/base/` for:
  - `opensearch` (StatefulSet, 1GB RAM bounds, persistent volumes)
  - `redis` (Deployment, persistent volumes)
  - `api`, `inference`, `worker` (Stateless Deployments)
- **Probes**: Added aggressive explicit `livenessProbe` and `readinessProbe` blocks to all stateless APIs to enable K8s self-healing.

## Developer Experience (DevEx)
- **Makefile Abstractions**: Abstracted complex `kubectl` and `kind` commands into simple targets (`make cluster-up`, `make deploy`, `make k9s`, `make port-forward`).
- **Runbooks**: Created `docs/RUNBOOK.md` detailing how to debug `CrashLoopBackOff`s, use the `k9s` terminal UI, and wipe corrupted PersistentVolumeClaims securely. 
- **Documentation**: Updated `README.md` to establish Kubernetes as the primary local deployment option and updated `GUIDE.md` to document the architectural reasoning behind the shift from Compose to K8s.
