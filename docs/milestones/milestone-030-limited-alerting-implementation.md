# Milestone 030 Limited Alerting Implementation

Started: 2026-09-10

Status: Complete. Offline validation, guarded activation, live verification and recovery evidence passed by 2026-09-11.

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

PR #6 embedded the exact canonical rules in the existing `prometheus-config` ConfigMap and added one `rule_files` entry. The existing Deployment already mounted that ConfigMap at `/etc/prometheus`; no workload template, image, RBAC, Service, storage, Grafana, Alertmanager, receiver, credential or application change was needed. The guarded candidate and Git patch reference merged at `f54b96138e9ac0521c6a854055dd1dd4ae0e1ed9`.

`manage-prometheus-alerts.ps1` defaults to read-only planning. It checks the exact live baseline, context, image, replicas, three healthy targets and current rule state; summarizes 24 hours of scoped target-count samples; performs server-side validation and shows the diff. Explicit `-Activate` is separate. It saves and verifies the live baseline ConfigMap before applying, restarts only Prometheus, requires both rules to be healthy and inactive, and automatically rolls back on failed post-change validation. Explicit rollback accepts only the known baseline recovery file. See the [activation review](../observability/limited-alerting-activation-review.md).

No cluster command, reload, rollout, traffic generation, failure injection or notification setup was performed while preparing the candidate. Live activation occurred only after the candidate was reviewed, CI was green, PR #6 was merged, `main` was synchronized, and Mike explicitly approved the mutation.

## Live activation evidence

At 2026-09-11 15:46:46 UTC, the guarded helper reconfirmed the exact baseline ConfigMap, three healthy Restaurant API targets, no loaded candidate alerts, and a 24-hour history containing 2,881 samples with minimum target count 3 and no below-three interval. Server-side dry-run passed and `kubectl diff` showed only the accepted `rule_files` entry and embedded rules.

Before mutation, the helper saved and re-read `C:\Users\wmsti\SignalForge-Backups\prometheus\alert-activation-20260911-154646Z.json`. The 1,587-byte recovery file has SHA-256 `BE7D39DD99715B70A99E5151D7E268EBA197F8F7C1F7E61D6C338468558403FA`.

The helper applied only `configmap/prometheus-config`, restarted only `deployment/prometheus`, and observed a successful rollout. Immediate and independent follow-up checks both reported three healthy targets and exactly two accepted rules with `health=ok` and `state=inactive`. The second plan classified the live ConfigMap as `candidate` and produced an empty diff against merged `main`. Automatic rollback was not invoked.

This proves live rule loading and healthy inactive evaluation under the normal three-target condition. It does not prove firing timing from a real incident, notification delivery, Prometheus self-health, or user-facing availability. No failure was injected and no Alertmanager or receiver exists.

## Remaining gates

- [x] Prepare offline rule candidates and source-level checks.
- [x] Run available local checks and document their limits.
- [x] Run pinned promtool checks and resolve any fixture/implementation failures.
- [x] Commit the offline change and obtain GitHub Actions evidence.
- [x] Complete final review and merge PR #5.
- [x] Present minimal rule wiring, observation, maintenance and rollback procedures for review.
- [x] Run and review the non-mutating live plan, including recent normal rollout/maintenance timing.
- [x] Explicitly accept the provisional five-minute warning and two-minute critical trial delays.
- [x] After separate approval, activate and validate live rule loading without implying delivered notifications.

Milestone 030 is complete. The next step is observation of naturally occurring behavior and periodic read-only rule-state checks before deciding whether a notification design is justified. Alertmanager, notification channels, performance thresholds, failure injection, and monitoring-system self-health remain outside this milestone.
