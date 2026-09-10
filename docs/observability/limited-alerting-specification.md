# SignalForge Limited Alerting Specification

Date: 2026-09-10

Status: Planning design accepted by Mike on 2026-09-10 for Milestone 029. No alerting is deployed by this plan.

Acceptance includes the provisional five-minute warning and two-minute critical delays, manual three-target baseline, monitoring blind spots, and future offline validation contract. It does not validate the expressions or authorize implementation, activation, or notification delivery. The accepted design was committed as `037d7c1` and merged through PR #4 at `1837868` on 2026-09-10. Subsequent [Milestone 030 offline preparation](../milestones/milestone-030-limited-alerting-implementation.md) is tracked separately; no live activation is implied.

Baseline: uploaded Git archive for `801174052d7eef801920870946f75dfa978768cd` (Milestone 028 complete).

## Purpose and boundaries

Answer one operational question: has successful Restaurant API scrape coverage remained below the expected three targets long enough to warrant investigation?

This milestone changes Markdown documentation only. It does not add executable rule files, recording rules, manifests, tests, dependencies, dashboards, exporters, self-scrapes, RBAC, credentials, notification channels, Alertmanager, or Grafana alert provisioning. It does not run cluster commands, reload Prometheus, generate traffic, or inject failures. Alert activation requires a separately approved implementation step.

The proposed future evaluator is the existing Prometheus instance: collection and evaluation would remain independent of Grafana. This is a design proposal, not a configuration change. Notification delivery and its architecture remain deferred. A future firing rule visible only in a UI must not be described as delivered notification coverage.

## Evidence and limits

- The reviewed scrape configuration discovers Restaurant API Pods in `forge-restaurant`, with 30-second scrape/evaluation intervals and a ten-second scrape timeout. It has no rule-file or Alertmanager configuration.
- Milestone 028 records three healthy targets, representative traffic, correct idle/missing-data presentation, and continued Prometheus collection while Grafana was stopped.
- Three is a manually maintained deployment baseline, not a desired-replica metric. Discovery labels do not provide deployment replica intent. Changing the intended replica count requires reviewing this design.
- The acceptance record is not a long-term traffic baseline or measured rollout-disruption distribution. Neither delay below is validated against normal rollout timing yet.
- Successful `/metrics` scraping is not proof of readiness, NodePort reachability, correct business responses, or an SLO. Failed scraping can indicate discovery, network, instrumentation, or application problems.
- Prometheus and Grafana share `forge-head` and its local NVMe dependency. If the evaluator stops, these rules cannot evaluate or deliver evidence of that failure. Independent monitoring remains a deferred coverage gap.

## Candidate conditions

| Candidate | Severity proposal | Condition | Continuous delay proposal |
| --- | --- | --- | --- |
| RestaurantScrapeCoverageDegraded | warning | More than zero but fewer than three healthy scoped targets | 5 minutes |
| RestaurantNoHealthyScrapeTargets | critical | Zero healthy scoped targets, including no scoped target series | 2 minutes |

Severity expresses investigation priority in this lab, not paging or a production SLA. The delays are provisional noise-control choices, not measured thresholds. Before activation, review ordinary rollout/replacement evidence; if unavailable, retain the explicit uncertainty and obtain operator acceptance of the trial delays.

Every selector must include `job="restaurant-api",namespace="forge-restaurant"`. Use a stable service-level alert identity with static `job`, `namespace`, and `severity` labels. Do not include changing healthy counts, Pod names, node names, or instance addresses in alert identity; put diagnostic values in annotations or dashboard context.

### Draft PromQL for later offline validation

These expressions are design text, not loaded rules or promtool-validated results.

Degraded coverage (`for: 5m` proposed):

```promql
(sum(up{job="restaurant-api",namespace="forge-restaurant"}) > 0)
and
(sum(up{job="restaurant-api",namespace="forge-restaurant"}) < 3)
```

No healthy scrape targets (`for: 2m` proposed):

```promql
(sum(up{job="restaurant-api",namespace="forge-restaurant"}) == 0)
or
absent(sum(up{job="restaurant-api",namespace="forge-restaurant"}))
```

Comparisons deliberately omit `bool`: a false condition must remove the vector element rather than return a zero-valued element that would still activate an alert. Aggregation yields a service-level label set; static rule labels must identify the job and namespace in future implementation. The missing-series branch is explicit and must not be copied into dashboards as null-to-zero replacement.

Both all-down and absent branches use the same empty expression label set so a transition between them can preserve the same alert identity. This behavior must be verified with the pinned evaluator before implementation. Discovered-all-down and absent discovery remain different diagnostic causes even though both warrant the same coverage alert.

The warning and critical conditions cannot be true simultaneously. Warning-to-critical escalation starts the critical rule's own delay. Recovery from zero to one or two healthy targets clears the critical condition and starts the warning rule's own delay; there can be a pending-only interval. This is intentional proposed behavior, not uninterrupted escalation coverage. Do not add `keep_firing_for` without revisiting overlap semantics.

The delay starts when the evaluator first observes the condition, not when the real failure occurs. Scrape cadence, discovery/staleness handling, evaluation alignment, and evaluator outages affect detection timing. A query/evaluation error is not an empty successful result; never claim these expressions catch evaluator failure.

## First response when implemented

1. Inspect the current Healthy and Discovered counts and per-Pod scrape timeline in the existing SignalForge dashboards. Distinguish explicit failed scrapes from missing discovery series.
2. Inspect target scrape errors and compare with the documented three-replica intent and any operator-known rollout, scale change, or maintenance.
3. Follow the existing [Restaurant API operator runbook](../runbooks/restaurant-api-operator-runbook.md) for evidence gathering and separately verify user-facing access before calling it an application outage.
4. Record the cause, duration, recovery, and whether the delay was useful. Do not automatically restart workloads, scale replicas, or modify discovery in response to an alert.

These are future response procedures, not instructions to run cluster checks during Milestone 029. Planned maintenance can meet these conditions; this design does not implement silencing or a maintenance calendar.

## Required future offline acceptance cases

Use synthetic promtool fixtures with the pinned Prometheus version before loading any rules. This milestone specifies the tests; it does not claim they were run.

| Scenario | Required result |
| --- | --- |
| Three successful scoped targets | Neither candidate active |
| One or two successful targets sustained | Warning pending, then firing after its delay; no critical |
| All discovered targets explicitly zero | Critical pending, then firing; no warning |
| No scoped series from startup | Critical after its delay, not a healthy zero fallback |
| Series become stale or disappear | Verify staleness transition and eventual critical; record detection timing |
| All-down transitions to absent series | Stable critical identity and pending continuity |
| Brief deficit below the applicable delay | Pending then cleared, never firing |
| Healthy count changes between one and two | Warning timer does not reset from changing annotation values |
| Warning escalates to zero; zero recovers to two | Independent timers, no simultaneous active conditions; pending-only gap documented |
| Recovery to three healthy targets | Both conditions clear on the next successful evaluation |
| More than three healthy targets during rollout | No coverage alert; extra discovery remains diagnostic context |
| Same metric in another job/namespace | Excluded from counts; must not mask scoped absence |
| No application traffic with healthy scrapes | Neither candidate activates solely because application counters are idle |
| Evaluator stopped or query failed | Explicitly outside detection guarantee; do not report missing-data handling as self-monitoring |

Future test evidence must include pending/firing boundary checks at the 30-second evaluation interval, static labels, annotation behavior, and counterexample cases. Use offline fixtures, not production failure injection, for rule correctness.

## Deferred signals

- HTTP 5xx percentage: establish representative traffic, a minimum request-volume gate, evaluation window, and actionable threshold first. Preserve idle/no-data behavior; do not reuse the old denominator floor.
- Latency: define useful per-route expectations and sufficient histogram observations before choosing a threshold. Middleware latency is not client-network latency.
- Node resource pressure, NVMe health, storage capacity, backup freshness, Grafana availability, and Prometheus self-health: the reviewed scrape configuration does not collect the necessary dedicated signals. Metrics Server availability does not automatically provide them to Prometheus.
- External service reachability and monitoring-system failure: require separately designed independent observation.
- Per-Pod failure alerts: deferred to keep the first set small; three healthy targets can mask an additional failed target during rollout, which remains visible in diagnostics.

No new platform or telemetry layer is implied by this deferral.

## Review and implementation gate

Milestone 029 can finish when the operator accepts the scope, provisional conditions/delays, manual replica baseline, uncovered failures, and future validation contract, and the documentation is reviewed and version controlled. Its completion does not claim alert-rule correctness, live activation, or delivered notifications.

Before a later implementation: explicitly approve evaluator ownership and activation scope; implement and pass the offline matrix; review observation evidence and trial delays; define rollback and maintenance handling; and identify exactly how rule state will be inspected. Any notification design or live failure exercise requires separate scope approval. Preserve current access, storage, RBAC, and provisioning boundaries unless separately authorized.

## References

- [Milestone 028 acceptance evidence](../milestones/milestone-028-lightweight-grafana.md)
- [Grafana dashboard semantics](grafana-dashboard-specification.md)
- [Prometheus scrape configuration](../../k8s/prometheus/prometheus-config.yaml)
- [Prometheus alerting rules](https://prometheus.io/docs/prometheus/latest/configuration/alerting_rules/)
- [Prometheus absence functions](https://prometheus.io/docs/prometheus/latest/querying/functions/#absent)
- [Prometheus rule unit testing](https://prometheus.io/docs/prometheus/latest/configuration/unit_testing_rules/)
