# Milestone 030 Limited Alerting Implementation

Started: 2026-09-10

Status: In progress. Offline package merged on 2026-09-10; activation candidate prepared but not activated.

## Baseline

Milestone 029 was accepted by Mike and merged in PR #4 at `1837868b17f58c41a0a700bc98a064226420497e`. The operator confirmed clean `main` synchronized with `origin/main`. GitHub metadata independently confirmed the merge, and all six Milestone 029 file blob hashes matched the locally reconstructed baseline. The local Git history is a reconstruction from the uploaded archive and reviewed patches, not a clone of the original commit graph.

The offline package was merged through PR #5 at `604e38e0aef369ffe803d85ff90b665c4af49b29`. The operator confirmed clean synchronized `main`, then created `codex/milestone-030-alert-activation-review` for the separately gated activation candidate.

## Offline increment

- Implement the two accepted candidate rules outside deployment manifests in `monitoring/alerts`.
- Preserve 30-second evaluation, scoped selectors, static service identity, and provisional five-minute/two-minute delays.
- Generate 19 offline fixture scenarios checking firing and pending behavior, labels, annotations, staleness, missing input, transitions, rollout cases, and scope isolation.
- Add strict source-level guardrails, negative regressions, an exact-version local runner, and a read-only offline CI job.
- Reconcile Milestone 029's now-completed commit/merge status.

The [alert package README](../../monitoring/alerts/README.md) contains execution instructions and limitations. Candidate expressions follow the [accepted design](../observability/limited-alerting-specification.md).

## Validation evidence

- Static scope validation passed; the current Prometheus configuration has no rule wiring or alert receivers, and Grafana alerting remains disabled.
- 13 source-level/negative regression tests passed. Expected negative-test failures verify runner fail-closed behavior; they are not PromQL test results.
- Existing repository manifest validation passed.
- All 17 existing Grafana regression tests passed.
- Full repository unittest discovery passed all 43 tests. Generated fixtures contain 122 firing-result assertions and 61 state-vector assertions across 19 scenarios; these subsequently passed actual promtool execution in CI.
- Python compilation, workflow shell syntax, relative documentation links, and the unchanged Kubernetes/application file boundary passed local checks.
- Promtool and Docker were not installed in the preparation workspace, and the official binary download timed out. No local PromQL execution is claimed; subsequent CI evidence is recorded below.

The CI job must execute `promtool check rules` and all generated `promtool test rules` cases with version 3.13.2. Failed fixtures must be investigated against the accepted design; do not weaken expectations merely to make CI pass. Static expression matching constrains the candidate design but cannot establish correctness in Prometheus.

## Pinned-evaluator CI evidence

On 2026-09-10, [GitHub Actions run 34542077003](https://github.com/wmstipes/The-Foundry-Initiative/actions/runs/34542077003) completed successfully for commit `29a6e31d3ee5a0f2d73a80d3eac44f8adbc117bb` in draft PR #5. Job `103086712923` passed all steps. Its real evaluator reported `promtool, version 3.13.2` (revision `bb5dff00cf8fdfbf5c65e0531aa835fa238a43a2`), `SUCCESS: 2 rules found`, and successful execution of all 19 generated scenarios. The 13 source-level regression tests also passed in that run.

This supplies synthetic rule-evaluation evidence, not a live rollout-timing measurement, ARM64 runtime test, delivered notification, or activation approval. The rules, fixtures, and workflow were unchanged by this evidence-only documentation update. PR #5 was subsequently reviewed and merged at `604e38e`.

## Activation-review increment

The next repository candidate embeds the exact canonical rules in the existing `prometheus-config` ConfigMap and adds one `rule_files` entry. The existing Deployment already mounts that ConfigMap at `/etc/prometheus`; no workload template, image, RBAC, Service, storage, Grafana, Alertmanager, receiver, credential or application change is needed.

`manage-prometheus-alerts.ps1` defaults to read-only planning. It checks the exact live baseline, context, image, replicas, three healthy targets and current rule state; summarizes 24 hours of scoped target-count samples; performs server-side validation and shows the diff. Explicit `-Activate` is separate. It saves and verifies the live baseline ConfigMap before applying, restarts only Prometheus, requires both rules to be healthy and inactive, and automatically rolls back on failed post-change validation. Explicit rollback accepts only the known baseline recovery file. See the [activation review](../observability/limited-alerting-activation-review.md).

No cluster command, reload, rollout, traffic generation, failure injection, notification setup or external Git write was performed while preparing this candidate. Local checks cannot claim the current live state.

## Remaining gates

- [x] Prepare offline rule candidates and source-level checks.
- [x] Run available local checks and document their limits.
- [x] Run pinned promtool checks and resolve any fixture/implementation failures.
- [x] Commit the offline change and obtain GitHub Actions evidence.
- [x] Complete final review and merge PR #5.
- [x] Present minimal rule wiring, observation, maintenance and rollback procedures for review.
- [ ] Run and review the non-mutating live plan, including recent normal rollout/maintenance timing.
- [ ] Explicitly accept or revise the provisional trial delays before activation.
- [ ] Only after separate approval, implement and validate live rule loading without implying delivered notifications.

Milestone 030 is not complete. The immediate next step is repository review and the read-only live plan, not activation. Alertmanager, notification channels, performance thresholds, failure injection, and monitoring-system self-health remain outside this increment.
