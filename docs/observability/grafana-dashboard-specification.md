# SignalForge Grafana Dashboard Specification

Date: 2026-09-10

Status: Design accepted for Milestone 027 on 2026-09-10; implementation validation pending

Data source UID: `signalforge-prometheus`

Baseline: Restaurant API v0.7.0 at repository commit `653ffa6`

These twelve candidate panels use only metric names and discovery labels present in the reviewed repository. They have been checked against source definitions, not executed against live Prometheus during planning. Validate their results and presentation in the implementation milestone.

## Shared behavior

Use folder `SignalForge`, the last 30 minutes by default, browser timezone, and refresh every 30 seconds. All rate queries use `[5m]`, preserving the repository's initial query convention. The title or description must make that fixed window visible when a user chooses a long dashboard range. Do not imply a five-minute rate is the total for the full selected range.

Scope every query to `job="restaurant-api",namespace="forge-restaurant"`. Use `traffic="application"` for application performance and `traffic="synthetic"` for probes and scrapes. Render legends with route, Pod, version, or status as appropriate. Avoid raw instance-address legends when a Pod label is available.

Use instant queries for current counts and metadata, and range queries for rates and timelines. Preserve gaps and show `No data` for absent values or NaN. Do not enable null-to-zero replacement or connect gaps in health timelines. A failed Prometheus request must remain a visible query error. Do not assign SLO colors to latency or error percentage before an SLO is agreed.

Three is the configured expected replica baseline. The dashboards cannot discover the desired replica count from Kubernetes today. Rate panels can remain populated briefly after a scrape failure because their five-minute windows include earlier samples; read them alongside current target health.

## Restaurant Overview

Dashboard UID: `signalforge-restaurant-overview`.

### Panel 1 Healthy and discovered targets

Stat panel with two instant queries:

```promql
sum(up{job="restaurant-api",namespace="forge-restaurant"})
```

```promql
count(up{job="restaurant-api",namespace="forge-restaurant"})
```

Label the results `Healthy` and `Discovered`, with `Expected 3` in the panel description. Summing `up` yields a real zero when discovered targets are all down; a completely missing job yields no data. Do not use a global zero fallback. Normal steady state is 3 healthy and 3 discovered. Treat fewer than 3 healthy as degraded and a count above 3 as a rollout or discovery change to inspect, rather than an automatic success. Extra discovered targets can appear during a rollout.

### Panel 2 Application request rate by route

Time series, requests/second, legend `method path`:

```promql
sum by (method, path) (
  rate(restaurant_api_requests_total{
    job="restaurant-api",namespace="forge-restaurant",traffic="application"
  }[5m])
)
```

An existing counter with no increments produces zero. Routes never exercised may have no series. Include the description `No series can mean this route has not been requested; check target health.`

### Panel 3 Application server error percentage

Stat with sparkline, percent from 0 to 100, using the following expression:

```promql
100 * (
  sum(rate(restaurant_api_requests_total{
    job="restaurant-api",namespace="forge-restaurant",
    traffic="application",status=~"5.."
  }[5m]))
  or
  (0 * sum(rate(restaurant_api_requests_total{
    job="restaurant-api",namespace="forge-restaurant",traffic="application"
  }[5m])))
)
/
(
  sum(rate(restaurant_api_requests_total{
    job="restaurant-api",namespace="forge-restaurant",traffic="application"
  }[5m])) > 0
)
```

The comparison deliberately omits `bool`: a positive denominator retains its actual request rate; zero is filtered out. The fallback creates zero errors only when an application request-rate series exists. With positive traffic and no 5xx series, the result is zero percent. With zero traffic or no usable samples, display `No data` with description `No application traffic or insufficient samples; inspect traffic and target health.`

This is a proposed refinement of the baseline query's denominator floor. A floor of 0.001 can bias percentages at very low rates. The dashboard expression avoids that bias and does not present an idle interval as an observed zero-error success. A successful query with missing data still needs the target-health panel to distinguish causes; a failed data-source query must remain an error.

### Panel 4 Application p95 latency by route

Time series, seconds with Grafana's automatic duration formatting:

```promql
histogram_quantile(
  0.95,
  sum by (le, path) (
    rate(restaurant_api_request_duration_seconds_bucket{
      job="restaurant-api",namespace="forge-restaurant",traffic="application"
    }[5m])
  )
)
```

Retain `le` while aggregating buckets across Pods before calculating the quantile. Never average per-Pod p95 values. This measures approximate middleware duration; it excludes client-network latency and may be coarse with few requests. NaN or absent output during inactivity is not zero latency.

### Panel 5 Version coverage among healthy targets

Instant table, version and reporting Pod count:

```promql
count by (version) (
  restaurant_api_info{job="restaurant-api",namespace="forge-restaurant"}
  and on (namespace, pod)
  (up{job="restaurant-api",namespace="forge-restaurant"} == 1)
)
```

Expected steady-state row: version `0.7.0`, count `3`. A rollout can show multiple versions. Filtering by current successful scrape reduces misleading metadata from a failed target, but normal Prometheus staleness rules still apply. This is observed version coverage, not Kubernetes rollout status.

### Panel 6 Analyze feature state by healthy Pod

Instant table with `pod`, `node`, and value:

```promql
restaurant_api_analyze_enabled{
  job="restaurant-api",namespace="forge-restaurant"
}
and on (namespace, pod)
(up{job="restaurant-api",namespace="forge-restaurant"} == 1)
```

Map 1 to `Enabled` and 0 to `Disabled`; disabled is not automatically a fault. Confirm the intended ConfigMap setting during implementation and inspect disagreement between Pods. Missing rows mean unobserved state, not disabled state.

## Scrape and Replica Diagnostics

Dashboard UID: `signalforge-scrape-diagnostics`.

### Panel 7 Per Pod scrape health

State timeline, legend `pod`:

```promql
up{job="restaurant-api",namespace="forge-restaurant"}
```

Map 1 to `Scrape successful` and 0 to `Scrape failed`. Leave absent intervals as gaps. When discovery removes a Pod, its series disappears after staleness handling; absence is not the same as an explicit failed scrape. Use Panel 1 for current counts. Pod-level scrape health does not verify NodePort access.

### Panel 8 Scrape duration by Pod

Time series, seconds:

```promql
scrape_duration_seconds{job="restaurant-api",namespace="forge-restaurant"}
```

Add the configured ten-second scrape timeout as a reference line. This metric is generated by Prometheus for application scrapes and requires no Prometheus self-scrape. A long scrape is diagnostic context, not a complete explanation of application latency.

### Panel 9 Scraped samples by Pod

Time series, sample count:

```promql
scrape_samples_scraped{job="restaurant-api",namespace="forge-restaurant"}
```

Use this to notice instrumentation changes or unexpected cardinality growth. Counts can grow legitimately when more route/status combinations are exercised. This is samples per scrape, not total TSDB series, storage consumption, or a full cardinality audit.

### Panel 10 Application request rate by Pod

Time series, requests/second:

```promql
sum by (pod) (
  rate(restaurant_api_requests_total{
    job="restaurant-api",namespace="forge-restaurant",traffic="application"
  }[5m])
)
```

Uneven traffic is not necessarily a load-balancing fault: connection reuse and a small request sample can skew distribution. Apply `rate` before summing so counter resets are handled per series.

### Panel 11 Synthetic traffic rate

Time series, requests/second, legend `path status`:

```promql
sum by (path, status) (
  rate(restaurant_api_requests_total{
    job="restaurant-api",namespace="forge-restaurant",traffic="synthetic"
  }[5m])
)
```

The current synthetic paths are `/health`, `/ready`, and `/metrics`. Classification is by path, so a manual request to these endpoints is also synthetic; this label is not proof of caller identity. Keep it separate from application demand.

### Panel 12 Unmatched application traffic

Time series, requests/second, legend `status`:

```promql
sum by (status) (
  rate(restaurant_api_requests_total{
    job="restaurant-api",namespace="forge-restaurant",
    traffic="application",path="unmatched"
  }[5m])
)
```

Request several distinct nonexistent paths during the bounded acceptance exercise and verify they share `path="unmatched"`. There may be no series before the first unmatched request. Do not add raw URLs or query strings as labels to improve this panel.

## Query and presentation acceptance

Check each expression in Prometheus before importing the dashboards. Verify selected units, labels, instant/range modes, data-source UID, and dashboard UID after file provisioning. Compare counts with the existing target helper and version endpoint evidence.

For error percentage, validate these cases using a small query fixture if the lab does not naturally produce errors: a positive denominator with no error series gives zero; 1 error per second over 10 requests per second gives 10 percent; a zero denominator gives no value; absent input gives no value. Include a very low positive rate to ensure no denominator-floor bias. Do not modify the Restaurant API to force an error solely for a dashboard check.

Exercise known routes long enough to span at least two 30-second scrapes and retain enough observations for the five-minute rate window. Confirm request rate and latency appear, synthetic traffic is separate, and unmatched paths remain bounded. Check missing data and datasource-error presentation with an isolated query fixture or temporary test data source rather than interrupting the production collector.

Observe refresh behavior and response time with both dashboards open for 30 minutes. Recheck Grafana and Prometheus resource usage and scrape health. Do not claim these panels prove backup freshness, node capacity, service reachability, or a service-level objective.

## Source references

- [Application metric definitions at commit 653ffa6](https://github.com/wmstipes/The-Foundry-Initiative/blob/653ffa6f730e61e4615d5e7fc188eb41c089df18/apps/restaurant-api/main.py)
- [Scrape configuration and discovery labels](https://github.com/wmstipes/The-Foundry-Initiative/blob/653ffa6f730e61e4615d5e7fc188eb41c089df18/k8s/prometheus/prometheus-config.yaml)
- [Existing five-minute PromQL baseline](https://github.com/wmstipes/The-Foundry-Initiative/blob/653ffa6f730e61e4615d5e7fc188eb41c089df18/docs/observability/prometheus-queries.md)

Suggested repository destination after agreement: `docs/observability/grafana-dashboard-specification.md`.
