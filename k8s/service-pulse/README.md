# Service Pulse Kubernetes candidate

This directory is a reviewed **candidate**, not a record of a live deployment. It defines one restricted `forge-pulse` namespace, two single-replica Deployments, and two internal ClusterIP Services. The board has no NodePort or Ingress. Istio injection is disabled for this first step; central logging and mesh enrollment will be reviewed separately.

Both Deployments pin the published Linux AMD64/ARM64 OCI index:

```text
wmstipes/signalforge-service-pulse:0.1.1@sha256:ef00b39bb93686ab087e254df4125622c29784ffff4ad2b74476064882af63e4
```

This is the corrected port-80 probe built from merge commit `5777e7c2a139a993e6e714ad22f64dadb6d28824` in [release run 35923087833](https://github.com/wmstipes/The-Foundry-Initiative/actions/runs/35923087833). Docker Hub reports Linux AMD64 manifest `sha256:abb558b6bb6b09e89d3fa2db09a63baeccfe061268e671bd6cc38c2ff4498f40` and ARM64 manifest `sha256:f3f5430cd5ce90c8395b7fcce734f85e933f3f0bffc876eaf56e63b30356e6b6` under the index.

Each Pod requests 50m CPU and 64Mi memory and is limited to 250m CPU and 128Mi memory. The two Pods together request 100m CPU and 128Mi memory; check live allocatable capacity, current allocations, and scheduling before applying. Both run as UID/GID 10001 with a read-only root filesystem, restricted Pod Security, no ServiceAccount token, and no granted Kubernetes RBAC. `/healthz` checks only the process. A ready Pod **does not** prove the Restaurant or probe connection works.

## Read-only preflight from the laptop

From the repository root in PowerShell, after pulling the reviewed merge:

```powershell
python .\scripts\validate-k8s-manifests.py
kubectl config current-context
kubectl get nodes -o wide
kubectl top nodes
kubectl describe nodes
kubectl get namespace forge-pulse --ignore-not-found --show-labels
kubectl get service restaurant-api -n forge-restaurant -o yaml
kubectl get endpointslices -n forge-restaurant -l kubernetes.io/service-name=restaurant-api -o wide
kubectl get deployment restaurant-api -n forge-restaurant -o wide
kubectl diff -f .\k8s\service-pulse\namespace.yaml
```

Confirm the context is the intended SignalForge cluster; nodes have enough allocatable headroom and no blocking taints; the Restaurant Service is `restaurant-api.forge-restaurant.svc.cluster.local` on ClusterIP port 80 with ready endpoints; and the target namespace is absent or matches this manifest. `kubectl top` reports recent use, while `kubectl describe nodes` shows allocatable and already requested resources. A nonzero `kubectl diff` exit can mean expected differences; inspect its output and distinguish that from an actual error. Live state may differ from tracked YAML. Do not apply if these facts do not match.

The new namespace must exist for a server-side dry-run of namespaced resources. After reviewing preflight and authorizing creation of this namespace, create it alone:

```powershell
kubectl apply --dry-run=server -f .\k8s\service-pulse\namespace.yaml
kubectl apply -f .\k8s\service-pulse\namespace.yaml
```

Then preview the four workload resources against the live API. Review each diff and the Pod Security admission result before authorizing the workload apply:

```powershell
kubectl apply --dry-run=server -f .\k8s\service-pulse\service-pulse-probe-deployment.yaml
kubectl apply --dry-run=server -f .\k8s\service-pulse\service-pulse-probe-service.yaml
kubectl apply --dry-run=server -f .\k8s\service-pulse\service-pulse-board-deployment.yaml
kubectl apply --dry-run=server -f .\k8s\service-pulse\service-pulse-board-service.yaml
kubectl diff -f .\k8s\service-pulse\service-pulse-probe-deployment.yaml
kubectl diff -f .\k8s\service-pulse\service-pulse-probe-service.yaml
kubectl diff -f .\k8s\service-pulse\service-pulse-board-deployment.yaml
kubectl diff -f .\k8s\service-pulse\service-pulse-board-service.yaml
```

## Scoped rollout and acceptance (after review)

Apply only the four reviewed resources, then check both single-replica rollouts and their actual connectivity:

```powershell
kubectl apply -f .\k8s\service-pulse\service-pulse-probe-deployment.yaml
kubectl apply -f .\k8s\service-pulse\service-pulse-probe-service.yaml
kubectl apply -f .\k8s\service-pulse\service-pulse-board-deployment.yaml
kubectl apply -f .\k8s\service-pulse\service-pulse-board-service.yaml
kubectl rollout status deployment/service-pulse-probe -n forge-pulse --timeout=180s
kubectl rollout status deployment/service-pulse-board -n forge-pulse --timeout=180s
kubectl get deployments,pods,services,endpointslices -n forge-pulse -o wide
kubectl logs deployment/service-pulse-probe -n forge-pulse --tail=30
kubectl port-forward -n forge-pulse service/service-pulse-board 18080:8080
```

In a second terminal open `http://127.0.0.1:18080/` and check `http://127.0.0.1:18080/api/status`. The probe should log fresh `functional_check` results with `result=ok`; the board should show a fresh sample and log `probe_read`. Match a board request ID to probe `checks_read`. A failed sample needs investigation of DNS, Service endpoints, policies and application logs; `/healthz` alone is insufficient. The board stores no history: probe replacement loses its in-memory samples. Central logging has not yet been deployed, so logs from a removed Pod may not remain available.

## Scoped rollback

If acceptance fails, remove only the four Pulse workloads and Services. Keep the namespace for inspection, then remove it only after checking it contains no unrelated objects:

```powershell
kubectl delete -f .\k8s\service-pulse\service-pulse-board-service.yaml
kubectl delete -f .\k8s\service-pulse\service-pulse-board-deployment.yaml
kubectl delete -f .\k8s\service-pulse\service-pulse-probe-service.yaml
kubectl delete -f .\k8s\service-pulse\service-pulse-probe-deployment.yaml
kubectl get all -n forge-pulse
```

No command in this runbook modifies `forge-restaurant`, enables Istio, or installs a logging stack.
