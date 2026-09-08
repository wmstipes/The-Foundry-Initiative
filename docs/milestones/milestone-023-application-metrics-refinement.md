# Milestone 023 - Application Metrics Refinement

Started: 2026-09-08

Completed: 2026-09-08

Status: Complete

## Goal

Turn the Restaurant API's raw request counter into a small set of useful, aggregation-safe signals for traffic, errors, and latency.

## Planned release

- Application version: `0.7.0`
- Docker image: `wmstipes/signalforge-restaurant-api:0.7.0`

## Implementation

- Added `traffic` to request-counter labels.
- Added `restaurant_api_request_duration_seconds` as a classic Prometheus histogram.
- Added explicit latency buckets from 5 milliseconds through 5 seconds.
- Classified `/health`, `/ready`, and `/metrics` as synthetic traffic.
- Classified other requests as application traffic.
- Changed the metric `path` label to use matched route templates.
- Collapsed unmatched URLs into `path="unmatched"` to protect label cardinality.
- Recorded requests that raise an unhandled exception with status `500`.
- Added tests for latency metrics, traffic classification, and unmatched-path normalization.
- Added baseline PromQL for target health, version coverage, request rate, 5xx percentage, p95 latency, average latency, and synthetic traffic.
- Updated Kubernetes release configuration and manifest validation for `0.7.0`.

## Metric labels

| Label | Meaning | Example |
|---|---|---|
| `method` | HTTP method | `GET` |
| `path` | Matched route template or `unmatched` | `/status` |
| `status` | HTTP response status | `200` |
| `traffic` | `application` or `synthetic` | `application` |

## Why a histogram

SignalForge runs three Restaurant API replicas. Histogram buckets can be summed across Pods before applying `histogram_quantile`, which makes an aggregate p95 latency query possible. Client-side summary quantiles cannot be meaningfully averaged across replicas.

## Metric-schema transition

Adding the `traffic` label creates a new request-counter series shape at the `0.7.0` rollout. Prometheus will age out the old `0.6.0` series normally, while the new baseline queries deliberately select only series carrying the new label. Rate and latency windows begin accumulating useful samples after the rollout.

## Acceptance criteria

- [x] Restaurant API tests pass locally.
- [x] Kubernetes manifest validation passes locally.
- [x] GitHub Actions tests and ARM64 image build pass.
- [x] Versioned image `0.7.0` is published.
- [x] The Kubernetes rollout completes with three ready Pods.
- [x] `/version` reports `0.7.0`.
- [x] Prometheus reports three healthy Restaurant API targets.
- [x] All three Pods expose `restaurant_api_info{version="0.7.0"}`.
- [x] Request-duration histogram buckets are queryable.
- [x] Application and synthetic traffic queries return separate results.
- [x] An arbitrary missing URL is recorded as `path="unmatched"` rather than its raw path.
- [x] Baseline PromQL queries are documented.

## Validation evidence

- Release commit: `a7f28dc`
- Release tag: `v0.7.0`
- Deployed image: `wmstipes/signalforge-restaurant-api:0.7.0`
- Smoke tests returned version `0.7.0` and reached multiple application replicas.
- Prometheus reported three healthy Restaurant API targets.
- Version coverage, per-Pod histogram, and traffic-classification queries returned the expected results.
- A NodePort request to `/missing/12345` returned HTTP 404.
- The bounded 404 query returned `{}` with value `1`; the empty label set is expected because the outer `sum` removes all labels.

## Baseline queries

See `docs/observability/prometheus-queries.md`.

## Release sequence

1. Run the local developer preflight.
2. Commit and push the implementation.
3. Confirm GitHub Actions is green.
4. Tag and push `v0.7.0`.
5. Confirm the versioned ARM64 image is published.
6. Deploy the Restaurant API.
7. Verify application and Prometheus behavior.
8. Complete the milestone documentation.
