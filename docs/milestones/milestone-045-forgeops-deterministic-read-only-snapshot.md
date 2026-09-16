# Milestone 045 — ForgeOps deterministic read-only snapshot

**Status:** Complete; implementation, publication, CI, read-only live acceptance, PR readiness, merge, closeout, and cleanup passed

**Started:** 2026-09-16

**Branch:** `codex/milestone-045-forgeops-snapshot`

**Baseline:** `main` at `aa178b0a4f63a4680d9f47063aec817807b9771e`

## Goal

Implement the Milestone 044 contract as a local Python command that collects, normalizes, evaluates, and renders a fixed read-only SignalForge health snapshot without broad discovery, sensitive-data access, cluster mutation, or AI-generated conclusions.

## Audience

- The SignalForge operator performing a repeatable point-in-time assessment.
- Technical reviewers evaluating deterministic operations and safety controls.
- A future evidence-grounded ForgeOps reasoning layer that can consume bounded observations without controlling collection scope.

## Delivered interface

~~~powershell
python -m forgeops snapshot `
  --kubeconfig <explicit-path> `
  --context kubernetes-admin@kubernetes `
  [--restaurant-url <explicit-base-url>] `
  [--workbench-url <explicit-base-url>] `
  [--format text|markdown]
~~~

The package also installs the `forgeops` entry point while preserving the existing `foundry-check` command. Local distribution metadata advances from `0.1.0` to `0.2.0`; no registry publication or release tag is part of this milestone.

## Implementation

The implementation separates:

1. fixed target identities and limits;
2. deny-by-default kubectl and HTTP runners;
3. selected-field collection and normalization;
4. deterministic evaluation;
5. presentation-independent result models; and
6. equivalent terminal and Markdown renderers.

The normalized schema identifier is `forgeops.snapshot/v1alpha1`. Each evaluated check has a stable identifier, `PASS`/`WARN`/`FAIL`/`UNKNOWN` status, observation, evidence source, collection time, and bounded expected, observed, or error-category details.

## Fixed evidence scope

- Nodes: `forge-head`, `forge-node-01`, `forge-node-02`, and `forge-node-03`.
- Deployments and selected Pods: Restaurant API (3), Prometheus (1), Grafana (1), Forge YAML Workbench (1), and Metrics Server (1).
- Routing: Restaurant API (3 ready endpoints), Prometheus (1), Grafana (1), and Workbench (1).
- API aggregation: one Available condition for `v1beta1.metrics.k8s.io`.
- Optional explicit HTTP: Restaurant API `/version`, `/health`, `/ready`, and `/status`; Workbench `/healthz`.

Optional endpoint groups are absent when their base URL is not supplied. They are never inferred or reported as passing without collection.

## Trust and safety controls

- The kubeconfig must resolve to one explicit regular file.
- The supplied context must exactly equal `kubernetes-admin@kubernetes`.
- `kubectl config current-context` must return that exact value before resource collection.
- Kubectl arguments are lists passed with `shell=False`; user input cannot become a resource, namespace, selector, output template, or raw API path.
- A closed operation enum maps only to the Milestone 044 read-command allowlist.
- Each kubectl call is limited to 10 seconds and 2 MiB of standard output.
- Each HTTP call is limited to 5 seconds and 64 KiB; redirects and URL credentials are rejected.
- The total collection budget is 90 seconds.
- Retained diagnostic text is redacted and limited to 2 KiB.
- Raw Kubernetes responses are immediately reduced to accepted fields; renderers never receive complete objects.
- Reports omit kubeconfig paths, credentials, addresses, headers, labels, annotations, environment values, volumes, and unrecognized HTTP fields.
- No retry, temporary Pod, log read, Event read, Secret or ConfigMap read, port-forward, remediation, or mutation exists.

## Deterministic interpretation

- `PASS` means selected evidence exactly matched the fixed expectation.
- `WARN` currently identifies a ready Pod with one or more restarts.
- `FAIL` identifies complete contrary evidence, including a NotReady node, replica shortfall, unhealthy Pod, pinned image-digest mismatch, routing mismatch, unavailable Metrics APIService, or mismatched HTTP response.
- `UNKNOWN` identifies incomplete evidence, including context mismatch, timeout, authorization or subprocess failure, malformed JSON, unexpected shape, duplicate identity, or oversized output.

Exit code `0` requires every required check to pass. Exit code `1` represents a complete collection with a warning or failure. Exit code `2` represents invalid invocation or incomplete required evidence and takes precedence over `FAIL` or `WARN`.

## Offline tests

Synthetic fixtures model the accepted four-node, five-Deployment, seven-Pod, four-Service, Metrics APIService, and five-endpoint baseline. Tests do not execute kubectl or contact a network.

Covered cases include:

- healthy baseline and stable ordering from shuffled fixture input;
- absent optional endpoint configuration;
- NotReady and duplicate Node evidence;
- Deployment replica shortfall;
- restarted, Pending, and digest-mismatched Pods;
- partially ready EndpointSlices;
- unavailable Metrics APIService;
- HTTP version mismatch;
- collection timeout and partial `UNKNOWN` results;
- exact-context failure before resource queries;
- malformed and oversized kubectl output;
- bounded redaction of diagnostic text;
- regular-file kubeconfig validation;
- URL and embedded-credential rejection;
- equivalent check semantics in both renderers; and
- deny-by-default rejection before subprocess execution.

The focused GitHub Actions workflow installs the local distribution, runs only offline ForgeOps tests, and confirms both command entry points remain available. It contains no kubeconfig, cluster credential, live HTTP target, package publication, image publication, or deployment step.

## Documentation

- README: current ForgeOps capability, invocation, output, and trust boundary.
- Architecture: implemented local component and data flow.
- Project status and roadmap: Milestone 045 local implementation state.
- Learning journal: implementation decisions and next gate.
- ForgeOps snapshot runbook: operator usage and failure handling.
- Milestone 044 record: completed closeout publication and cleanup state.

The Wiki source remains unchanged because the repository remains authoritative and publication is outside this milestone.

## Release, deployment, and rollback

- No container image, image tag, registry package, release tag, or application release.
- No Kubernetes manifest, ServiceAccount, RBAC, workload, Service, or cluster change.
- No Wiki publication or live-cluster access during local implementation.

Rollback is a normal source revert of the focused implementation commit. Because the command is local and read-only, rollback requires no cluster recovery. An operator may also uninstall the editable local package without affecting the cluster.

## Local acceptance

1. Branch begins at exact baseline `aa178b0a4f63a4680d9f47063aec817807b9771e`.
2. Only the accepted targets and operations can reach the runners.
3. Context mismatch stops before any resource query.
4. Selected fields are normalized before evaluation and rendering.
5. Offline healthy and failure fixtures produce deterministic status, ordering, and exit semantics.
6. Terminal and Markdown reports contain the same checks and omit restricted data.
7. Existing `foundry-check` behavior remains intact.
8. All repository tests, package installation checks, applicable validators, and whitespace validation pass.
9. No live Kubernetes or HTTP request occurs before separate approval.

## Publication and CI evidence

- Pull request: #29.
- Published branch: `codex/milestone-045-forgeops-snapshot`.
- Implementation commit: `4ae5ddedde9ce51efab94adf0f4f94b25829ac7b`.
- Implementation tree: `0561e2ddc1c54af6fd12d840828fb820d4ad6893`, exactly matching the locally reviewed tree at commit `b15329b08a27df1ff27fa48ba0707a5ba6a60d5f`.
- Live-evidence reconciliation branch head: `377b8439ded59b5f6c48b2bf6b848a991ba2f079`.
- Reviewed branch-head tree: `c879d164e726a20c418e48eb931731102e61d51e`.
- ForgeOps CI runs `35128781478` and `35129577800` completed successfully before merge.

## Read-only live acceptance

Read-only live acceptance was separately approved and passed on 2026-09-16. The operator ran the exact published commit from a detached temporary worktree, confirmed the published commit and tree before execution, and supplied one explicit kubeconfig, the exact `kubernetes-admin@kubernetes` context, and the two previously reviewed application base URLs.

The snapshot collected at `2026-09-16T17:36:52Z` reported:

- Kubernetes client `v1.36.1` and server `v1.36.4`.
- All four expected Nodes with exactly matching Ready evidence.
- All five Deployments with expected desired, updated, ready, and available replicas and exact configured images.
- Seven selected Pods across five workload selectors, all Running and container-ready with zero restarts.
- Exact configured-image matches for every Pod and runtime digest matches for both digest-pinned workloads.
- Three ready Restaurant API endpoints plus one each for Prometheus, Grafana, and Workbench, with no not-ready or unknown endpoints.
- One Available Metrics APIService condition.
- HTTP 200 and exact bounded fields for Restaurant API `/version`, `/health`, `/ready`, and `/status`, plus exact `ok` for Workbench `/healthz`.

The deterministic summary was `33 PASS, 0 WARN, 0 FAIL, 0 UNKNOWN`, overall `PASS`, exit code `0`. The command displayed its scope and redaction boundary and did not expose the kubeconfig path, credentials, addresses, headers, complete objects, or unrecognized HTTP fields.

The acceptance used only the implemented read-operation allowlist and five explicit HTTP GETs. It did not read logs, Events, Secrets, ConfigMaps, broad namespace state, or arbitrary API paths; create a temporary Pod; start a port-forward; change a workload; or mutate the cluster.

## Merge evidence

- PR #29 was marked ready only after separate approval and the offline, CI, exact-tree, and read-only live-acceptance evidence passed.
- PR #29 merged into `main` at `3e9851da0351e1e01f90c5e38b534e5bbade929d` on 2026-09-16 at 13:43:27 EDT.
- The merge tree is `c879d164e726a20c418e48eb931731102e61d51e`, exactly matching the reviewed branch-head tree.
- Branch head `377b8439ded59b5f6c48b2bf6b848a991ba2f079` is an ancestor of the merge commit.
- ForgeOps CI push run `35129953752` completed successfully on the merge commit.
- No package, image, tag, manifest, deployment, Wiki, or cluster resource changed as part of readiness or merge.

## Closeout and cleanup evidence

- Closeout PR #30 merged into `main` at `f714d2567bce35ee90f4a5ff9ab0edd5fe9194ef`.
- The implementation and closeout branches were removed locally and remotely after separate approval.
- Only the intentionally preserved remote branches `feature/foundry-check-cli` and `feature/project-status` remained.

## Gated delivery workflow

1. Planning — approved.
2. Local implementation — approved and complete.
3. Branch publication and draft PR — approved and complete through draft PR #29.
4. Package or image release — not applicable and not authorized.
5. Deployment — not applicable and not authorized.
6. Read-only live acceptance — approved and passed with 33 checks and exit code `0`.
7. Pull-request readiness — approved and complete.
8. Merge — complete at `3e9851da0351e1e01f90c5e38b534e5bbade929d`.
9. Closeout — complete through PR #30 at `f714d2567bce35ee90f4a5ff9ab0edd5fe9194ef`.
10. Cleanup — complete; both Milestone 045 branches were removed locally and remotely.
