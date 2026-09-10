# Milestone 030 Limited Alerting Implementation

Started: 2026-09-10

Status: In progress, offline preparation only. Promtool execution, CI, and activation review pending.

## Baseline

Milestone 029 was accepted by Mike and merged in PR #4 at `1837868b17f58c41a0a700bc98a064226420497e`. The operator confirmed clean `main` synchronized with `origin/main`. GitHub metadata independently confirmed the merge, and all six Milestone 029 file blob hashes matched the locally reconstructed baseline. The local Git history is a reconstruction from the uploaded archive and reviewed patches, not a clone of the original commit graph.

Working branch: `codex/milestone-030-limited-alerting-offline`.

## Scope of this increment

- Implement the two accepted candidate rules outside deployment manifests in `monitoring/alerts`.
- Preserve 30-second evaluation, scoped selectors, static service identity, and provisional five-minute/two-minute delays.
- Generate 19 offline fixture scenarios checking firing and pending behavior, labels, annotations, staleness, missing input, transitions, rollout cases, and scope isolation.
- Add strict source-level guardrails, negative regressions, an exact-version local runner, and a read-only offline CI job.
- Reconcile Milestone 029's now-completed commit/merge status.

The [offline package README](../../monitoring/alerts/README.md) contains execution instructions, known limitations, and the next approval gate. Candidate expressions follow the [accepted design](../observability/limited-alerting-specification.md).

## Validation evidence

- Static scope validation passed; the current Prometheus configuration has no rule wiring or alert receivers, and Grafana alerting remains disabled.
- 13 source-level/negative regression tests passed. Expected negative-test failures verify runner fail-closed behavior; they are not PromQL test results.
- Existing repository manifest validation passed.
- All 17 existing Grafana regression tests passed.
- Full repository unittest discovery passed all 43 tests. Generated fixtures contain 122 firing-result assertions and 61 state-vector assertions across 19 scenarios; these are pending actual promtool execution.
- Python compilation, workflow shell syntax, relative documentation links, and the unchanged Kubernetes/application file boundary passed local checks.
- Promtool and Docker were not installed in the preparation workspace, and the official binary download timed out. No actual PromQL execution, pinned-rule timing validation, or workflow run is claimed.

The CI job must execute `promtool check rules` and all generated `promtool test rules` cases with version 3.13.2. Failed fixtures must be investigated against the accepted design; do not weaken expectations merely to make CI pass. Static expression matching constrains the candidate design but cannot establish correctness in Prometheus.

## Unchanged runtime boundary

No file under `k8s/`, application code, existing deployment helper, storage resource, access policy, or credential is changed by this increment. No cluster command, reload, rollout, traffic generation, fault injection, notification setup, or external Git write was performed during patch preparation. The uploaded source and prior acceptance record are not a fresh live-cluster inspection.

## Remaining gates

- [x] Prepare offline rule candidates and source-level checks.
- [x] Run available local checks and document their limits.
- [ ] Run pinned promtool checks and resolve any fixture/implementation failures.
- [ ] Review and commit the offline change; obtain GitHub Actions evidence.
- [ ] Review rollout timing and explicit trial-delay acceptance before activation.
- [ ] Present minimal rule wiring, observation, maintenance, and rollback procedures for operator approval.
- [ ] Only after separate approval, implement and validate live rule loading without implying delivered notifications.

Milestone 030 is not complete. The immediate next step is offline test execution, not deployment. Alertmanager, notification channels, performance thresholds, and monitoring-system self-health remain outside this increment.
