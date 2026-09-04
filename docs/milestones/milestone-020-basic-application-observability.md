# Milestone 020 — Basic Application Observability

Date: 2026-09-04

## Result

Added basic Prometheus-style application observability to the SignalForge Restaurant API.

## Application version

0.6.0

## New endpoint

/metrics

## What changed

- Added `prometheus-client` to the Restaurant API runtime dependencies
- Added Prometheus-style request metrics
- Added application info metrics
- Added analyze-feature state metric
- Added `/metrics` endpoint
- Added test coverage for the metrics endpoint
- Updated application version from `0.5.0` to `0.6.0`
- Updated Kubernetes manifests for the `0.6.0` release
- Updated validation expectations for the new release version

## Metrics added

- `restaurant_api_requests_total`
- `restaurant_api_info`
- `restaurant_api_analyze_enabled`

## Confirmed

- Local Restaurant API tests passed
- Kubernetes manifest validation passed
- GitHub Actions completed successfully
- Versioned Docker image was built and pushed
- Kubernetes deployed the `0.6.0` image
- `/version` returned `0.6.0`
- `/status` returned healthy application status
- `/metrics` returned Prometheus-style metrics

## Why it matters

The application can now expose runtime signals instead of only responding to health checks.

This is the first step toward real observability.

## Lesson learned

Health checks answer whether the service is alive.

Metrics begin answering how the service is behaving over time.

## Next

Install or configure a metrics collector so the cluster can scrape and retain application metrics.
