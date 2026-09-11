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

---

## 2026-09-09 - Milestone 025

### What I worked on

Compared practical persistent-storage designs for the SignalForge Prometheus server and converted the result into an explicit implementation and recovery plan before touching the NVMe or live cluster.

### What I learned

- Persistence and high availability are separate properties. A local PV preserves data across Pod replacement but cannot follow the workload to another node.
- PV node affinity lets the Kubernetes scheduler understand a local disk's physical location; a plain `hostPath` does not express that relationship as safely in a multi-node cluster.
- Prometheus's TSDB favors a local POSIX filesystem and does not support NFS, even when network storage initially appears more flexible.
- A retention-size limit needs free space for the WAL, head chunks, and compaction. The application limit should stay below the filesystem's full capacity.
- A missing-mount safeguard matters as much as the normal mount path. Otherwise, a valid directory can silently redirect heavy writes back to the SD card.
- Backups must leave the storage node and be restore-tested; `Retain` protects data from Kubernetes deletion behavior but is not a backup.

### What was difficult

The main tradeoff was accepting that the lightest design is intentionally node-bound. Adding NFS or a distributed storage platform would appear to improve mobility, but it would either conflict with Prometheus storage guidance or add more operational burden than this single workload justifies.

It also required keeping the planning milestone distinct from implementation. The approved design is now documented, but the repository still truthfully describes the live collector as ephemeral.

### What I finished

- Selected a static `local` PV on a dedicated ext4 partition of the `forge-head` NVMe.
- Defined capacity, retention, StorageClass, reclaim, affinity, and workload-strategy decisions.
- Documented Pod, node, NVMe, deletion, and missing-mount failure behavior.
- Defined weekly off-node cold backups, recovery objectives, restore validation, migration, and rollback.
- Created a strict pre-deployment acceptance gate for Milestone 026.
- Made no live cluster or storage changes.

### Next small step

Implement Milestone 026 by verifying the NVMe identity first, then creating and validating the partition, mount, static storage resources, Prometheus cutover, backup, and rollback path.


## 2026-09-10 - Milestone 026

Completed the NVMe-backed Prometheus cutover, Pod-replacement persistence test, off-node cold backup, isolated restore analysis, port-forward check, and rollback/return drill. The installed disk was a Samsung 950 PRO 512GB rather than the originally planned 2 TB device; inventory and destructive-testing gates caught that discrepancy before deployment.

Lessons: a metric exposed by Prometheus is not automatically stored in its query database; readiness must read `/metrics` when self-scraping is absent. Windows PowerShell nested-shell quoting broke a restore check, so direct command arguments replaced it. A try/finally recovery path restored persistent collection even when execution policy blocked a test script. Use the established process-scoped execution-policy invocation for operator helpers.

Recovery evidence must stay precise: six blocks were listed and the newest analyzed, but full service recovery and the one-hour RTO were not measured. Weekly backups remain manual. The temporary rollback Pod became Ready; its target check was blocked, while the restored persistent collector passed all three-target checks and loaded six retained blocks.

Next small step: plan lightweight Grafana and dashboard requirements for proposed Milestone 027.

## 2026-09-10 - Milestone 030 offline preparation

Milestone 029 was accepted and merged at `1837868`. The next increment translates its two scrape-coverage conditions into unactivated rules and synthetic test cases.

Engineering notes: alert identity belongs in stable labels; changing diagnostic counts belong in annotations. Failed scrapes, missing discovery series, and stopped evaluation are different situations. A transition between warning and critical conditions starts the other rule's independent delay, so an explicit pending-only interval is part of the accepted design. The critical expression's absent branch does not return a healthy-target count and must not be described as one.

Source-level tests and inactive-configuration guards passed, but they do not prove PromQL behavior. The preparation environment lacked promtool and Docker; subsequent [GitHub Actions run 34542077003](https://github.com/wmstipes/The-Foundry-Initiative/actions/runs/34542077003) supplied the missing evidence for commit `29a6e31`: real promtool 3.13.2 validated both rules and passed all 19 scenarios. PR #5 later merged at `604e38e`. Offline correctness does not establish operational delay suitability or authorize activation.

## 2026-09-10 - Milestone 030 activation review preparation

The activation candidate reuses the ConfigMap already mounted at `/etc/prometheus`: one embedded canonical rule file and one exact `rule_files` entry are sufficient, with no Deployment, RBAC, storage, Grafana or receiver change.

The safety boundary belongs in the operator path as well as the manifest. The helper therefore defaults to inspection, classifies the live ConfigMap by normalized hashes, requires the known context/image/replica/target baseline, shows recent coverage history and `kubectl diff`, and stops before mutation. Explicit activation first writes a validated recovery object; failed post-change verification triggers rollback. Repository desired state, evaluator-visible firing state and delivered notification are three different claims and must remain separate.

Next small step: review the repository diff and read-only live plan. Only a separate operator decision can authorize activation.
