# Milestone 044 — ForgeOps read-only health snapshot design

**Status:** Design published in draft PR #27; read-only live feasibility acceptance passed; PR readiness remains separately gated

**Started:** 2026-09-16

**Branch:** `codex/milestone-044-forgeops-snapshot-design`

**Baseline:** `main` at `90c4b369516881943ed3c00d1070f7c70b5fc7ae`

## Goal

Define the first bounded ForgeOps collection contract before implementing it: a local command that gathers an attributable, read-only snapshot of selected SignalForge health evidence without changing the cluster, reading secret data, or treating missing evidence as healthy.

Milestone 044 is a design milestone. It does not implement or run the collector. A later implementation milestone may proceed only from this reviewed contract.

## Why this is the smallest useful increment

The repository already has several adjacent tools, but none provides this contract:

- `scripts/forge.ps1 status` prints the current context, nodes, and Restaurant namespace resources, but its output is not normalized and the same dispatcher exposes deployment and other mutating commands.
- `scripts/forge.ps1 smoke` creates and deletes a temporary curl Pod, so it is intentionally excluded from a read-only snapshot.
- `foundry-check` evaluates local repository readiness rather than Kubernetes runtime health.
- The operator runbook defines a recovery sequence and health standard, but an operator must still collect and correlate each observation manually.

A reviewed collection and interpretation boundary is therefore required before adding another operational command or an AI reasoning layer.

## Audience

- The SignalForge operator who needs a quick, repeatable assessment.
- Technical reviewers evaluating the project's operational and safety discipline.
- A future ForgeOps evidence-ingestion layer that must distinguish observations from conclusions.

## Proposed command boundary

The later implementation should be a separate local command rather than a new mode inside the mixed read/write `forge.ps1` dispatcher. Its provisional interface is:

~~~powershell
python -m forgeops snapshot `
  --kubeconfig <explicit-path> `
  --context kubernetes-admin@kubernetes
~~~

Both the kubeconfig path and context are required. The collector must pass them explicitly to every kubectl invocation and verify the resolved current context before any resource query. It must not silently fall back to an ambient context.

The default output is a concise terminal summary. A Markdown rendering may be written to standard output for explicit redirection or sharing. Both views derive from the same normalized snapshot and preserve the same status, ordering, evidence, and redaction rules.

## Fixed collection scope

The initial contract is SignalForge-specific rather than a generic Kubernetes scanner.

### Nodes

- Expected nodes: `forge-head`, `forge-node-01`, `forge-node-02`, and `forge-node-03`.
- Evidence: node identity and Ready condition.
- The first increment does not collect addresses, capacity, allocatable resources, taints, labels beyond identity, or complete Node objects.

### Workloads

| Namespace | Deployment | Expected replicas | Purpose |
| --- | --- | ---: | --- |
| `forge-restaurant` | `restaurant-api` | 3 | Primary application |
| `forge-observability` | `prometheus` | 1 | Historical application metrics |
| `forge-observability` | `grafana` | 1 | Visualization |
| `forge-tools` | `forge-yaml-workbench` | 1 | Browser-local YAML inspection |
| `kube-system` | `metrics-server` | 1 | Current resource metrics |

For each allowlisted Deployment, the normalized snapshot records desired, updated, ready, and available replica counts plus the configured container image references.

For Pods selected only for those Deployments, it records name, phase, scheduled node, container readiness, restart counts, waiting or terminated reason when present, and runtime image identifiers. It does not include environment variables, mounted data, command arguments, annotations, complete labels, or complete Pod objects.

### Routing and API availability

The initial Service allowlist is:

| Namespace | Service | Required evidence |
| --- | --- | --- |
| `forge-restaurant` | `restaurant-api` | Three ready application endpoints |
| `forge-observability` | `prometheus` | One ready endpoint |
| `forge-observability` | `grafana` | One ready endpoint |
| `forge-tools` | `forge-yaml-workbench` | One ready endpoint |

- Allowlisted Services are evaluated through their matching EndpointSlices.
- Ready, not-ready, and unknown endpoint counts remain distinct.
- Restaurant API routing, Workbench routing, and observability routing are not collapsed into one result.
- The `v1beta1.metrics.k8s.io` APIService availability condition is collected without retrieving Metrics Server logs.

### Optional application endpoints

Endpoint checks require explicit operator-provided base URLs. The collector must never discover an address and then make an unapproved network request.

Allowed paths are:

- Restaurant API: `/version`, `/health`, `/ready`, and `/status`.
- Forge YAML Workbench: `/healthz`.

Redirects are not followed, response bodies are size-bounded, and each request has an independent timeout. Failure to configure an optional base URL is reported as `UNKNOWN` or not collected according to the final output contract; it is never reported as passing.

## Normalized result model

The future implementation will create one versioned in-memory snapshot before rendering. The initial schema identifier is `forgeops.snapshot/v1alpha1`.

Every check contains:

- a stable check identifier;
- one of `PASS`, `WARN`, `FAIL`, or `UNKNOWN`;
- a concise observation;
- the evidence source and collection time in UTC;
- an optional expected value and observed value; and
- an optional bounded error category.

The collector must keep evidence and interpretation separate. For example, `readyReplicas=2` is evidence; `FAIL: restaurant-api has 2 of 3 expected ready replicas` is the deterministic interpretation.

`UNKNOWN` is required when evidence is missing, incomplete, timed out, malformed, unauthorized, or outside the configured boundary. The renderer must not replace `UNKNOWN` with a healthy overall result.

## Stable ordering

Results are ordered as follows:

1. invocation and context validation;
2. nodes in the expected order above;
3. workloads in the table order above;
4. Pods sorted by namespace, owning Deployment, and Pod name;
5. routing checks sorted by namespace and Service name;
6. Metrics APIService availability; and
7. optional HTTP endpoints in their allowlisted order.

Timestamps do not influence ordering. Markdown and terminal output must render the same normalized result sequence.

## Exit codes

| Code | Meaning |
| ---: | --- |
| `0` | All required observations were collected and passed. |
| `1` | Collection completed, but at least one deterministic warning or failure was observed. |
| `2` | Invocation was unsafe or invalid, the context did not match, or required evidence could not be collected completely. |

An incomplete collection takes precedence over an otherwise healthy-looking subset. Detailed results may still be rendered before exit code `2` when doing so does not expose restricted data.

## Read-operation allowlist

The implementation may invoke only argument-array equivalents of these operations, always with the explicit kubeconfig and context:

- `kubectl config current-context`
- `kubectl version -o json`
- `kubectl get nodes -o json`
- `kubectl get deployment <allowlisted-name> -n <allowlisted-namespace> -o json`
- `kubectl get pods -n <allowlisted-namespace> -l <fixed-selector> -o json`
- `kubectl get endpointslices -n <allowlisted-namespace> -l kubernetes.io/service-name=<allowlisted-service> -o json`
- `kubectl get apiservice v1beta1.metrics.k8s.io -o json`

The exact Service names and Pod selectors must be constants in the implementation and covered by tests. User input must not become a resource name, selector, namespace, output template, raw API path, or shell fragment.

## Forbidden operations and data

The collector must not invoke or expose:

- `apply`, `create`, `delete`, `patch`, `replace`, `edit`, `scale`, `set`, `annotate`, `label`, `taint`, `cordon`, `drain`, `uncordon`, `rollout`, or `run`;
- `exec`, `attach`, `cp`, `port-forward`, `proxy`, `logs`, `describe`, or arbitrary `get --raw` paths;
- Secret or ConfigMap objects, ServiceAccount tokens, kubeconfig contents, client certificates, private keys, environment values, or mounted file contents;
- broad namespace enumeration, cluster-wide workload discovery, Events, admission objects, or RBAC object contents;
- shell evaluation, command strings assembled from user input, kubectl plugins, or dynamically discovered executables; or
- any remediation, restart, deployment, rollback, or confirmation prompt that can mutate state.

The command must not call the existing mutating smoke-test helper.

## Timeouts and failure behavior

- Verify that the kubeconfig exists as a regular file before invoking kubectl.
- Require an exact context match and stop before resource collection on mismatch.
- Limit each kubectl operation to 10 seconds and its captured standard output to 2 MiB.
- Limit each HTTP operation to 5 seconds and its response body to 64 KiB.
- Limit categorized standard-error text retained for evaluation to 2 KiB after redaction.
- Limit the complete first implementation to a 90-second collection budget.
- Reject non-JSON kubectl output, oversized output, duplicate identities, and unexpected schema shapes.
- Preserve partial safe evidence while marking the required collection incomplete.
- Do not retry authentication, authorization, context, or malformed-data failures automatically.
- Permit at most one bounded retry for an explicitly classified transient connection failure in a future revision; the first implementation should default to no retry.

## Redaction and report boundary

Terminal and Markdown reports omit:

- kubeconfig paths and contents;
- tokens, certificate data, credentials, and authorization headers;
- node and Pod IP addresses;
- complete object JSON, labels, annotations, environment values, and volume details;
- HTTP response headers and unrecognized response fields; and
- raw subprocess standard error beyond a categorized, length-bounded summary.

Node and Pod names, allowlisted resource names, image references, readiness state, restart counts, expected public release versions, and bounded endpoint response fields are permitted evidence for this private-lab report.

Markdown output is an explicit trust-boundary crossing because it may be redirected to a durable or shared file. The report must begin with the schema version, UTC collection time, target context, scope statement, and redaction statement. It must not claim continuous monitoring, compliance, or complete cluster health.

## Testing strategy for implementation

The implementation must separate collection, normalization, evaluation, and rendering so unit tests can use fixtures without executing kubectl or contacting a cluster.

Required offline cases include:

- healthy four-node and five-workload baseline;
- missing or NotReady node;
- Deployment replica shortfall;
- Pending, Failed, not-ready, or restarted Pod;
- configured and runtime image mismatch;
- missing, empty, partially ready, or unknown EndpointSlice state;
- unavailable Metrics APIService;
- application version, health, readiness, or status mismatch;
- absent optional endpoint configuration;
- kubeconfig or context mismatch;
- timeout, authorization failure, missing resource, malformed JSON, oversized output, and partial collection;
- deterministic ordering across shuffled fixture input;
- identical terminal and Markdown semantics;
- redaction of restricted fields and bounded error output;
- exit-code precedence; and
- a deny-by-default command test proving that no unlisted kubectl argument vector can execute.

Unit tests must mock the command and HTTP runners. A test failure must not fall back to a live kubectl invocation.

## Read-only live feasibility acceptance

Live feasibility is a separate approval gate after local design review and before PR readiness. If approved, the operator will run only the reviewed read commands needed to confirm that the required JSON fields exist and the allowlisted endpoint responses have the expected bounded shapes.

Live acceptance will not run the future collector, create a Pod, read logs, inspect Secrets or ConfigMaps, start a port-forward, publish a report, or mutate a resource. Any unavailable field or permission changes the design rather than prompting broader discovery.

Live feasibility was separately approved and completed on 2026-09-16.

### Publication evidence

- Published branch: `codex/milestone-044-forgeops-snapshot-design`.
- Published commit: `c0cbfabaf9af3f37d43586985fec51bfc3a21f20`.
- Draft pull request: #27.
- The published and locally reviewed trees matched exactly at `f542f306b209231da101f1a8f79d3aa1688bb787`.
- GitHub reported no workflow runs or commit statuses for the documentation-only head commit at publication review time.

### Kubernetes evidence

- The operator supplied one explicit kubeconfig and the exact context resolved as `kubernetes-admin@kubernetes` before resource collection.
- Client `v1.36.1` queried server `v1.36.4`.
- `forge-head`, `forge-node-01`, `forge-node-02`, and `forge-node-03` each had exactly one Ready condition with status `True`.
- All five allowlisted Deployments matched expected desired, updated, ready, and available replica counts: Restaurant API 3; Prometheus, Grafana, Workbench, and Metrics Server 1 each.
- All seven selected Pods were Running and container-ready with zero restarts and no waiting or terminated reason.
- The three Restaurant API Pods reported one consistent runtime image digest; configured and runtime evidence was present for every selected workload.
- Restaurant API had three ready EndpointSlice endpoints. Prometheus, Grafana, and Workbench each had one. None was not-ready or unknown.
- `v1beta1.metrics.k8s.io` had exactly one Available condition with status `True` and reason `Passed`.

### HTTP evidence

- The operator explicitly provided both base URLs; no address was discovered from cluster data.
- Redirect following was disabled, each request had a five-second timeout, and each body was limited to 64 KiB.
- Restaurant API `/version`, `/health`, `/ready`, and `/status` returned HTTP 200 with the expected release `0.7.0`, health, readiness, service, district, open-state, and enabled-analysis fields.
- Workbench `/healthz` returned HTTP 200 with the exact body `ok`.
- All five endpoint checks passed.

### Fail-closed preflight evidence

An initial operator attempt assumed a default Windows kubeconfig path that did not exist. Context and resource collection therefore remained incomplete and was classified as `UNKNOWN`, equivalent to exit code `2`; its empty follow-on displays were excluded from health evidence. The corrected acceptance resolved exactly one existing operator-configured `KUBECONFIG` file, verified the target context, and ran the collection atomically. No cluster resource changed during either attempt.

The accepted combined Kubernetes and HTTP result is `PASS`, equivalent to exit code `0` under this contract.

## Release and deployment impact

- No package or application version changes.
- No release tag or container image.
- No workflow, application source, Kubernetes manifest, ServiceAccount, RBAC, Service, or workload changes.
- No cluster deployment, rollout, restart, or other mutation.
- No Wiki source or live Wiki change.

## Documentation updates

Milestone 044 updates only the milestone record, roadmap, architecture, project status, learning journal, and stale Milestone 043 cleanup state. Operator commands and runbooks remain unchanged because the collector does not yet exist.

## Rollback

Rollback is documentation-only: revert the focused planning change or revise this contract before implementation. A failed live feasibility check requires a design correction; it does not justify changing cluster permissions or runtime resources.

## Deterministic acceptance checks

1. The branch begins at exact baseline `90c4b369516881943ed3c00d1070f7c70b5fc7ae`.
2. Every proposed health conclusion maps to a named, allowlisted evidence source.
3. Required context, resource identities, ordering, statuses, exit codes, timeouts, redaction, and failure behavior are explicit.
4. The allowlist contains only read operations and the forbidden list covers mutation and sensitive-data paths.
5. Expected resources and replica counts match the repository manifests at the baseline.
6. Milestone 043 merge, Wiki commit, and branch cleanup are reconciled in current-state documentation.
7. The diff contains no application, workflow, script, dependency, test, manifest, Wiki-source, or runbook change.
8. Wiki validation, focused Wiki tests, relevant repository tests, and whitespace validation pass unchanged.
9. No live cluster or HTTP request occurs without separate live-acceptance approval.

## Gated delivery workflow

1. Planning — approved.
2. Local implementation — approved; documentation-only implementation complete.
3. Branch publication and draft PR — approved and complete in draft PR #27 at `c0cbfab`.
4. Image release — not applicable; no image action is authorized.
5. Deployment — not applicable; no cluster mutation is authorized.
6. Read-only live feasibility acceptance — approved and passed on 2026-09-16.
7. Pull-request readiness — not authorized.
8. Merge — not authorized.
9. Closeout — not authorized.
10. Cleanup — not authorized.
