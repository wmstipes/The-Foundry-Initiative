# Learning Journal

Use this journal to capture progress without requiring polished prose.

## Entry template

### Date

### What I worked on

### What I learned

### What was difficult

### What I finished

### Next small step

---

## 2026-07-18

### What I worked on

Created the initial structure and guiding documents for The Foundry Initiative.

### What I learned

A project can begin with structure and intent before its first technical implementation is selected.

### What was difficult

Starting something meaningful can create pressure to make it large or perfect immediately.

### What I finished

Established a repository scaffold, roadmap, project vision, contribution workflow, and architecture placeholder.

### Next small step

Choose a first artifact that can be completed and demonstrated in a short development cycle.

---

## 2026-09-08

### What I worked on

Built SignalForge from an initial Raspberry Pi Kubernetes lab into a repeatable application and observability platform. The work progressed through Milestones 001-023 and culminated in Restaurant API `0.7.0` with lightweight Prometheus collection.

### What I learned

- Small milestones make a multi-component platform easier to build, test, and explain.
- A Kubernetes Service is useful for stable application access, but Prometheus should discover and scrape each replica directly when per-Pod counters matter.
- Application metrics and the Kubernetes Metrics API solve different problems; installing Prometheus does not make `kubectl top` available.
- Histogram buckets can be aggregated across replicas, making them appropriate for fleet-wide latency percentiles.
- Metric labels need the same design discipline as an API. Route templates and a bounded `unmatched` value prevent uncontrolled cardinality.
- Automated tests, manifest validation, pinned images, and operator helpers turn successful commands into a repeatable engineering workflow.
- Cross-platform quoting deserves explicit testing when PowerShell launches commands inside Linux containers.

### What was difficult

The most subtle problem was distinguishing a healthy metrics collector from broader cluster resource monitoring. Another challenge was correcting the Prometheus target-check helper after nested PowerShell and shell quoting produced an unterminated-string failure.

Release sequencing also required care: application changes, GitHub Actions, a version tag, the ARM64 image build, Kubernetes deployment, smoke tests, and Prometheus validation each had to complete in the right order.

### What I finished

- Deployed and operated a four-node Kubernetes cluster.
- Released Restaurant API `0.7.0` as three healthy replicas.
- Added application CI, ARM64 image publishing, versioned Kubernetes manifests, and validation automation.
- Added laptop-based deployment, smoke-test, status, log, and metrics helpers.
- Created and exercised an operator runbook.
- Deployed a least-privilege Prometheus collector with three healthy Pod targets.
- Added request latency, application-versus-synthetic traffic classification, and label-cardinality protection.
- Verified the live application, automatic target discovery, and baseline PromQL queries.

### Next small step

Select Milestone 024. Evaluate whether Kubernetes Metrics Server provides enough operational value to justify its footprint in the Raspberry Pi cluster.

---

## 2026-09-08 - Milestone 024

### What I worked on

Evaluated Kubernetes Metrics Server for SignalForge, repaired the cluster's kubelet serving-certificate configuration, and enabled current node and Pod resource visibility.

### What I learned

- Prometheus application metrics and the Kubernetes resource Metrics API are complementary rather than interchangeable.
- A healthy kubelet can still present a serving certificate that is unsuitable for a secure metrics client.
- `rotateCertificates: true` controls kubelet client-certificate rotation; `serverTLSBootstrap: true` is separately required for signed serving certificates.
- Core Kubernetes does not automatically approve kubelet serving CSRs because an operator must confirm that the requested DNS names and IP addresses belong to the requesting node.
- A TLS-authenticated request can correctly return HTTP 401. That response proves the certificate and connection succeeded while unauthenticated application access was rejected.
- `kubectl top` is useful for immediate operational checks, while historical analysis still belongs in Prometheus.

### What was difficult

The initial failure appeared to be a Metrics Server installation problem, but testing exposed three underlying identity issues: Windows SSH used the wrong username, the cluster nodes lacked durable hostname mappings, and kubelets served self-signed certificates containing only DNS SANs. Repairing the trust chain required verified SSH host keys, one-node-at-a-time kubelet changes, and manual inspection of every serving CSR.

### What I finished

- Restored verified, passwordless administrative SSH from `forge-head` to all workers.
- Made the SignalForge hostname mappings durable against cloud-init regeneration.
- Enabled kubelet serving-certificate bootstrap locally and in the kubeadm ConfigMap.
- Reviewed and approved four node-specific `kubernetes.io/kubelet-serving` CSRs.
- Verified Kubernetes-CA trust and InternalIP SANs on every kubelet endpoint.
- Deployed pinned Metrics Server v0.9.0 without `--kubelet-insecure-tls`.
- Enabled `kubectl top nodes` and `kubectl top pods` for all four nodes.
- Measured Metrics Server at 4m CPU and 21 MiB memory and retained it.

### Next small step

Plan persistent NVMe-backed Prometheus storage before replacing the intentionally ephemeral `emptyDir` volume.
