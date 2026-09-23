# SignalForge Service Pulse (source candidate)

Service Pulse is a small, noncritical functional-check board for the SignalForge lab. It has two modes from one image:

- `PULSE_MODE=probe`: every 30 seconds, GET the Restaurant API's internal `/menu` endpoint with a 2-second timeout; keep only 20 samples in memory. A successful response must contain a restaurant name and a specials list. `/checks` exposes the bounded samples.
- `PULSE_MODE=board`: serve the local board and GET the probe's `/checks` endpoint when viewed, then every 15 seconds. The board identifies samples older than 90 seconds as stale and never equates a missing probe with a restaurant failure.

Both modes expose `/healthz`. Board-to-probe reads and functional checks emit one-line JSON to stdout with UTC observation time, result and a generated request/sample ID. They do not log response bodies, incoming URL parameters or raw exception text from failed network calls. The board sends an `X-Request-ID` that appears in both board and probe logs; the menu check's `sampleId` ties its result to the board sample. There is no Kubernetes API credential, write endpoint, external ingress, persistence or remediation behavior.

## Local validation

From the repository root:

```sh
python -m unittest discover -s apps/service-pulse/tests -v
python -m py_compile apps/service-pulse/main.py
```

The PR CI smoke-tests two non-root, read-only containers exchanging requests and builds AMD64/ARM64 images **without publishing**. The probe's Restaurant request is expected to fail in this isolated smoke test; the test verifies that the failure is recorded as a fresh sample and the board can still read it. This does not demonstrate a live Restaurant API connection on the Pi cluster.

**No image is published and no cluster objects are changed by a pull request or merge.** The Python base image is pinned to the digest resolved by the successful Service Pulse CI build at `54737c29ba6db2cde65fefe4add90d0bfcafe07a`. The separate image release workflow is manual-only, accepts the exact full reviewed commit SHA on `main`, only publishes version `0.1.0` to `wmstipes/signalforge-service-pulse`, checks that the versioned tag is absent, and uses the protected `release` environment. It records the published OCI index digest after checking that AMD64 and ARM64 manifests are present. Confirm the Docker Hub repository and release credentials are available before approving a manual run. A successful non-publishing build produces no deployable image digest.

After a separately reviewed publication, draft Kubernetes manifests with the verified index digest. The manifest review must include: a separate `forge-pulse` namespace; only two one-replica Deployments and ClusterIP Services; no ServiceAccount token; non-root/read-only filesystem; resource requests/limits; readiness/liveness; port-forward-only board access; exact image digest; and scoped rollback. Check actual node capacity and confirm the Restaurant API Service DNS/port before deployment.

Central log storage (Loki/Alloy) and Istio enrollment are separate gates. Limit initial ingestion to `forge-pulse`; set retention, storage budget, RBAC and recovery before logging rollout. Verify ARM64 images, Kubernetes and kernel/CNI compatibility, Pod Security admission, proxy resource use and mesh rollback before enrolling these two workloads. Keep `forge-restaurant` out of the initial mesh exercise.

Operator acceptance: read the board, correlate a board `probe_read` request ID with probe `checks_read`, find a menu `functional_check` sample in both the board and logs, then replace a Pulse Pod and verify its prior log line is still queryable in the central store. A sample timestamp is the last observation, not an outage start time. The memory-only board history is expected to reset after probe replacement.
