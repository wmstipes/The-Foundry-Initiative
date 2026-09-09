# Milestone 024 - Kubernetes Metrics Server Evaluation

Started: 2026-09-08

Completed: 2026-09-08

Status: Complete

## Goal

Determine whether Kubernetes Metrics Server provides enough operational value for its resource footprint on the SignalForge Raspberry Pi cluster. Enable `kubectl top` securely if the cluster meets the prerequisites, measure the live component, and retain or remove it based on evidence.

## Decision

Retain one Metrics Server replica.

The live workload consumed 4m CPU and 21 MiB memory while reporting all four nodes. That footprint is small relative to SignalForge's 16 allocatable CPU cores and approximately 39 GiB of allocatable memory, and the component immediately improved node and Pod troubleshooting.

Metrics Server remains separate from Prometheus:

- Metrics Server supplies recent CPU and memory samples to Kubernetes APIs and autoscaling clients.
- Prometheus retains and queries application time series over a longer window.

## Baseline

Before the milestone:

- `v1beta1.metrics.k8s.io` did not exist.
- `kubectl top nodes` returned `Metrics API not available`.
- The aggregation-layer proxy certificate flags were present on kube-apiserver.
- Kubelet webhook authentication and authorization were enabled.
- Kubelet serving certificates were self-signed, contained only a DNS SAN, and could not validate an InternalIP connection.

## Kubelet PKI repair

SignalForge did not use the testing-only `--kubelet-insecure-tls` workaround. Instead, the underlying node identity and trust configuration was repaired.

1. Restored durable short-name mappings on `forge-head` while accounting for cloud-init's `manage_etc_hosts` behavior.
2. Read each worker's ED25519 SSH host-key fingerprint directly from its console.
3. Compared those fingerprints with keys presented over the network before adding them to `known_hosts`.
4. Confirmed passwordless SSH and non-interactive sudo from `forge-head` to each worker.
5. Backed up `/var/lib/kubelet/config.yaml` on every node.
6. Added top-level `serverTLSBootstrap: true` one node at a time.
7. Restarted kubelet and kept each node cordoned until its serving request was validated.
8. Inspected each `kubernetes.io/kubelet-serving` CSR before approval.
9. Confirmed the requester, groups, usages, subject, and SANs belonged only to the named node.
10. Approved the exact CSR and verified the resulting certificate was issued by `CN=kubernetes`.
11. Confirmed HTTPS access to every kubelet InternalIP succeeded with the Kubernetes CA and returned HTTP 401 for the unauthenticated health request.
12. Added `serverTLSBootstrap: true` to the kubeadm-managed `kube-system/kubelet-config` ConfigMap for lifecycle durability.

## Verified kubelet identities

| Node | InternalIP | Serving certificate SANs | TLS result |
|---|---|---|---|
| `forge-head` | `192.168.243.110` | `DNS:forge-head`, `IP:192.168.243.110` | HTTP 401 after successful verification |
| `forge-node-01` | `192.168.243.111` | `DNS:forge-node-01`, `IP:192.168.243.111` | HTTP 401 after successful verification |
| `forge-node-02` | `192.168.243.112` | `DNS:forge-node-02`, `IP:192.168.243.112` | HTTP 401 after successful verification |
| `forge-node-03` | `192.168.243.113` | `DNS:forge-node-03`, `IP:192.168.243.113` | HTTP 401 after successful verification |

## Metrics Server implementation

- Version: `v0.9.0`
- Image: `registry.k8s.io/metrics-server/metrics-server:v0.9.0`
- Namespace: `kube-system`
- Replicas: 1
- Collection interval: 15 seconds
- Address preference: `InternalIP,ExternalIP,Hostname`
- Kubelet trust: `--kubelet-certificate-authority=/var/run/secrets/kubernetes.io/serviceaccount/ca.crt`
- Insecure kubelet flag: absent
- Resource requests: 100m CPU and 200 MiB memory
- API: `metrics.k8s.io/v1beta1`
- Upstream `components.yaml` SHA-256: `1cec29a5267809306a2c6ec74a3e449abbb705b4a8beed0c8a1963910f72c79b`

The APIService retains the upstream default `insecureSkipTLSVerify: true` for the API server-to-Metrics Server connection because Metrics Server dynamically generates its own serving certificate. This is distinct from kubelet certificate verification. A durable serving certificate and APIService CA bundle can be considered separately if that additional control becomes worthwhile.

## Acceptance criteria

- [x] Metrics Server version is compatible with Kubernetes 1.36.
- [x] The image runs on ARM64.
- [x] Aggregation-layer and kubelet webhook prerequisites are enabled.
- [x] All four kubelets present Kubernetes-CA-signed serving certificates.
- [x] Every serving certificate includes the correct hostname and InternalIP SANs.
- [x] Metrics Server validates kubelets with the Kubernetes CA.
- [x] `--kubelet-insecure-tls` is absent.
- [x] The Deployment rolls out with one ready Pod and zero restarts.
- [x] `v1beta1.metrics.k8s.io` reports Available.
- [x] Recent Metrics Server logs contain no certificate, authorization, or scrape errors.
- [x] `kubectl top nodes` returns all four nodes.
- [x] `kubectl top pods -n forge-restaurant` returns all three application Pods.
- [x] Metrics Server's live footprint is measured.
- [x] Retain or remove decision is documented.

## Validation evidence

Metrics Server Pod:

```text
READY 1/1
STATUS Running
RESTARTS 0
NODE forge-node-03
```

Observed cluster usage:

| Node | CPU | Memory |
|---|---:|---:|
| `forge-head` | 178m | 2627 MiB |
| `forge-node-01` | 20m | 1116 MiB |
| `forge-node-02` | 25m | 1200 MiB |
| `forge-node-03` | 27m | 1177 MiB |

Observed workload usage:

| Workload | CPU | Memory |
|---|---:|---:|
| Metrics Server | 4m | 21 MiB |
| Prometheus | 2m | 30 MiB |
| Each Restaurant API Pod | 1-2m | 40-41 MiB |

Resource usage is a point-in-time sample rather than a capacity guarantee. The upstream 100m CPU and 200 MiB requests remain unchanged until longer observation justifies tuning.

## Operational follow-up

- Keep kubelet serving-certificate requests under manual approval.
- Validate every future CSR's requester, signer, usages, subject, and SAN ownership.
- Use the repository deployment and test helpers for repeatable Metrics Server operation.
- Use `kubectl top` for current resource visibility, not historical monitoring.
- Reassess limits or high availability only if the cluster's workload or reliability requirements materially change.

## Next milestone

Milestone 025 should plan persistent NVMe-backed storage for Prometheus before changing the live collector.
