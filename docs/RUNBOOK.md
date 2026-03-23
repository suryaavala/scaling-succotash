# Enterprise B2B Search - Kubernetes Runbook

This runbook covers Day 2 operations for the local `kind` Kubernetes cluster.

## 1. Using `k9s` (Kubernetes UI)

`k9s` is a terminal-based UI to interact with your Kubernetes clusters.
- Launch it via: `make k9s`
- **Navigation**:
  - `:dp` - View Deployments
  - `:ss` - View StatefulSets
  - `:po` - View Pods
  - `:svc` - View Services
- **Actions** (while hovering over a Pod):
  - `l` - View logs
  - `s` - Shell into the container
  - `d` - Describe the pod
  - `ctrl-d` - Delete the pod

## 2. Debugging a CrashLoopBackOff

If a pod fails to start and enters a `CrashLoopBackOff` state:

1. **Describe the Pod** to see event history and exit codes:
   ```bash
   kubectl describe pod <pod-name>
   ```
   Look at the `Events` section at the bottom for scheduling or probe failures.

2. **Check the Logs**:
   ```bash
   kubectl logs <pod-name>
   ```
   If the container died too quickly, check the previous instance's logs:
   ```bash
   kubectl logs <pod-name> --previous
   ```

3. **Common Causes**:
   - **OOMKilled**: Memory limits exceeded. Increase limits in the manifest.
   - **Liveness Probe Failed**: The application is deadlocking or taking too long to start. Increase `initialDelaySeconds`.
   - **Configuration Error**: A missing environment variable or secret.

## 3. Wiping and Resetting State (Data Corruption)

If `opensearch` or `redis` data becomes corrupted, here is how you reset their state cleanly:

### OpenSearch (HostPath Mapping)
OpenSearch relies on a direct `hostPath` mount to your laptop's `./data/opensearch` directory for cross-compatibility with Docker Compose.
To wipe OpenSearch:
1. Shut down the cluster: `make cluster-down`
2. Delete the local directory: `rm -rf ./data/opensearch/*`
3. Restart the cluster: `make cluster-up && make docker-build-local && make deploy`

### Redis (PersistentVolumeClaim)
Redis utilizes a standard Kubernetes PVC. To wipe it:
1. `kubectl delete pvc redis-data-redis-0`
2. `kubectl delete statefulset redis`
3. `make deploy` (Forces recreation of an empty volume instance).

## 4. Useful `kubectl` Cheat Sheet

Here are vital native `kubectl` commands for observing and manipulating the cluster directly:

- **Get everything in the namespace:**
  `kubectl get all`
- **Tail live logs from a specific deployment (e.g. Gateway API):**
  `kubectl logs -l app=gateway-api -f`
- **Execute an interactive bash shell inside a running pod:**
  `kubectl exec -it deployment/gateway-api -- /bin/bash`
- **Force a rolling restart of a deployment (zero downtime):**
  `kubectl rollout restart deployment/gateway-api`
- **Check resource utilization (CPU/Memory) of pods:**
  `kubectl top pods`
- **View detailed node capacity and allocations:**
  `kubectl describe node kind-worker`

## 5. Useful `kind` Cheat Sheet

When managing the overarching docker-in-docker `kind` infrastructure:

- **List active clusters:**
  `kind get clusters`
- **Retrieve all control-plane and worker Docker nodes:**
  `docker ps -f label=io.x-k8s.kind.cluster=kind`
- **Export all cluster logs for offline debugging:**
  `kind export logs ./kind-debug-logs`
- **Manually load a newly built image without the Makefile:**
  `kind load docker-image scaling-succotash-gateway_api:latest --name kind`

## 6. Localhost Port Mappings Reference

Through `kind-config.yaml` and `NodePort` injections, you can securely access K8s services natively on your local machine without `kubectl port-forward`:

- `http://localhost:8000` -> **Gateway API**
- `http://localhost:8001` -> **Inference LLM Service**
- `http://localhost:8501` -> **Streamlit Frontend**
- `http://localhost:9200` -> **OpenSearch Database**
- `http://localhost:16686` -> **Jaeger UI**
- `http://localhost:6379` -> **Redis** *(Note: Internal cluster only by default, requires native port-forward `kubectl port-forward svc/redis 6379:6379` if external GUI connection is needed)*
