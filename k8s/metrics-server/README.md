# SignalForge Kubernetes Metrics Server

These manifests deploy Kubernetes Metrics Server for current CPU and memory visibility through the resource metrics API.

## Scope

- Namespace: `kube-system`
- Deployment: `metrics-server`
- Image: `registry.k8s.io/metrics-server/metrics-server:v0.9.0`
- Replicas: 1
- Collection interval: 15 seconds
- Kubelet address order: `InternalIP,ExternalIP,Hostname`
- Kubelet certificate validation: Kubernetes service-account CA
- Resource requests: 100m CPU and 200 MiB memory

The Deployment deliberately does not use `--kubelet-insecure-tls`. Every SignalForge kubelet uses a Kubernetes-CA-signed serving certificate with its node hostname and InternalIP in the certificate SANs.

The manifests are based on the official v0.9.0 `components.yaml` release asset, whose published SHA-256 digest is `1cec29a5267809306a2c6ec74a3e449abbb705b4a8beed0c8a1963910f72c79b`. SignalForge splits the upstream resources into reviewable files, adds project labels, and adds the kubelet CA argument.

## Prerequisites

- Kubernetes aggregation layer enabled
- Kubelet webhook authentication and authorization enabled
- `serverTLSBootstrap: true` in the kubeadm kubelet ConfigMap and every node's `/var/lib/kubelet/config.yaml`
- Manually reviewed and approved `kubernetes.io/kubelet-serving` CSRs for all four nodes
- Metrics Server-to-kubelet connectivity on TCP 10250

Core Kubernetes does not automatically approve kubelet serving CSRs. Review requester, signer, usages, subject, and SAN ownership before approving a current or future request.

## Resources

- `metrics-server-service-account.yaml` creates the workload identity.
- `metrics-server-rbac.yaml` contains the upstream RBAC resources required by the aggregated API.
- `metrics-server-service.yaml` exposes Metrics Server inside the cluster.
- `metrics-server-deployment.yaml` runs the pinned ARM64-compatible image and validates kubelet certificates with the cluster CA.
- `metrics-server-api-service.yaml` registers `metrics.k8s.io/v1beta1` with the Kubernetes aggregation layer.

`insecureSkipTLSVerify: true` on the APIService is part of the upstream default manifest and applies only to the API server's connection to Metrics Server's dynamically generated serving certificate. It is distinct from the prohibited `--kubelet-insecure-tls` flag. Managing an APIService CA bundle and durable Metrics Server serving certificate is outside Milestone 024.

## Deploy and validate

From the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\forge.ps1 metrics-server-deploy
powershell -ExecutionPolicy Bypass -File .\scripts\forge.ps1 metrics-server-status
powershell -ExecutionPolicy Bypass -File .\scripts\forge.ps1 top
```

The deployment helper waits for the rollout and APIService, validates the security arguments, and confirms that all four node metrics are available.

## Purpose and limitations

Metrics Server keeps only the latest CPU and memory samples needed by Kubernetes APIs and autoscaling. It is not a historical monitoring system and does not replace Prometheus application metrics.
