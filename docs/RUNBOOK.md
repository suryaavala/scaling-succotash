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

## 3. Wiping and Resetting State

If the `opensearch` or `redis` data becomes corrupted, you may need to wipe the PersistentVolumeClaims (PVCs).

1. Delete the PVCs:
   ```bash
   kubectl delete pvc opensearch-data-opensearch-0 redis-data
   ```
2. Delete the pods to force recreation and rebinding to new empty volumes:
   ```bash
   kubectl delete pod opensearch-0
   kubectl delete deployment redis
   ```
3. Re-apply the manifests:
   ```bash
   make deploy
   ```
4. Re-ingest the data as the search index will be empty.
