# SignalForge Service Pulse

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

The Python base image is pinned to a digest. Version `0.1.0` was published on 2026-09-23 from main commit `9a0c8a917f1e10e1a30596205c951e0adfde4e90` by [release workflow run 35921316979](https://github.com/wmstipes/The-Foundry-Initiative/actions/runs/35921316979). Its Docker Hub OCI index is `wmstipes/signalforge-service-pulse:0.1.0@sha256:f8fdc560c2cc04c7f99b9702378eb162b6a2c7c7d3a2a05e5472b2e68fd9acff` with Linux AMD64 and ARM64 manifests. **Do not deploy 0.1.0:** its Restaurant probe uses port 8000, while the tracked `restaurant-api` ClusterIP Service exposes port 80. The source here corrects the probe to use the Service port; a new image is required before cluster use.

The corrected `0.1.1` image was published on 2026-09-23 from merge commit `5777e7c2a139a993e6e714ad22f64dadb6d28824` by [release workflow run 35923087833](https://github.com/wmstipes/The-Foundry-Initiative/actions/runs/35923087833). Its verified Linux AMD64/ARM64 OCI index is `wmstipes/signalforge-service-pulse:0.1.1@sha256:ef00b39bb93686ab087e254df4125622c29784ffff4ad2b74476064882af63e4`. Do not retag or reuse `0.1.0` for the correction.

The live Kubernetes manifests in `k8s/service-pulse` use the verified index digest. The separate `forge-pulse` namespace contains two one-replica Deployments and ClusterIP Services, with no ServiceAccount token, non-root/read-only filesystem, resource requests/limits, readiness/liveness, port-forward-only board access and scoped rollback. See its README for the live acceptance record and phased change review. Recheck actual node capacity and the Restaurant API Service DNS/port before future changes. Merging manifests does not apply cluster objects.

Central log storage (Loki/Alloy) and Istio enrollment are separate gates. Limit initial ingestion to `forge-pulse`; set retention, storage budget, RBAC and recovery before logging rollout. Verify ARM64 images, Kubernetes and kernel/CNI compatibility, Pod Security admission, proxy resource use and mesh rollback before enrolling these two workloads. Keep `forge-restaurant` out of the initial mesh exercise.

Operator acceptance: read the board, correlate a board `probe_read` request ID with probe `checks_read`, find a menu `functional_check` sample in both the board and logs, then replace a Pulse Pod and verify its prior log line is still queryable in the central store. A sample timestamp is the last observation, not an outage start time. The memory-only board history is expected to reset after probe replacement.
