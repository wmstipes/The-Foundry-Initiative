# SignalForge Prometheus Query Baseline

These queries form the initial PromQL baseline for the SignalForge Restaurant API.

The examples use a five-minute range. Low-traffic application queries may be empty until requests have occurred within that window.

## Target health

Count healthy Restaurant API scrape targets:

```promql
count(up{job="restaurant-api"} == 1)
```

Expected result: `3`

Show each target and its discovery labels:

```promql
up{job="restaurant-api"}
```

## Version coverage

Count Pods exposing version `0.7.0`:

```promql
count(restaurant_api_info{version="0.7.0"})
```

Expected result after rollout: `3`

## Application request rate

Show requests per second by method, route, and status while excluding probes and Prometheus scrapes:

```promql
sum by (method, path, status) (
  rate(restaurant_api_requests_total{traffic="application"}[5m])
)
```

## Application server-error percentage

Calculate the percentage of application requests returning HTTP 5xx responses:

```promql
100
*
(
  sum(rate(restaurant_api_requests_total{traffic="application",status=~"5.."}[5m]))
  or vector(0)
)
/
clamp_min(
  sum(rate(restaurant_api_requests_total{traffic="application"}[5m])),
  0.001
)
```

The denominator floor prevents division by zero during idle periods.

## Application p95 latency

Calculate the 95th-percentile request duration by route across all Restaurant API Pods:

```promql
histogram_quantile(
  0.95,
  sum by (le, path) (
    rate(restaurant_api_request_duration_seconds_bucket{traffic="application"}[5m])
  )
)
```

The `le` label must remain in the aggregation because it identifies each histogram bucket boundary.

## Average application latency

Calculate average request duration across application traffic:

```promql
sum(rate(restaurant_api_request_duration_seconds_sum{traffic="application"}[5m]))
/
clamp_min(
  sum(rate(restaurant_api_request_duration_seconds_count{traffic="application"}[5m])),
  0.001
)
```

## Synthetic traffic rate

Inspect Kubernetes probes and Prometheus scrape traffic separately:

```promql
sum by (path, status) (
  rate(restaurant_api_requests_total{traffic="synthetic"}[5m])
)
```

Synthetic paths are `/health`, `/ready`, and `/metrics`.

## Label-cardinality protection

Known FastAPI routes use their route templates as the `path` label. Requests that do not match a route use `path="unmatched"` instead of recording arbitrary URL paths.

This prevents paths such as `/missing/1`, `/missing/2`, and `/missing/3` from creating separate time series.
