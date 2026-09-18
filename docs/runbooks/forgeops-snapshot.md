# ForgeOps read-only snapshot runbook

This runbook operates the local ForgeOps snapshot command introduced in Milestone 045. The command collects a bounded point-in-time view of named SignalForge resources. It is not continuous monitoring, a complete cluster-health claim, a compliance check, or a remediation tool.

Read the [ForgeOps operator and learning guide](../guides/forgeops-operator-learning-guide.md)
for the consolidated architecture, command map, execution modes, exit domains,
and trust boundaries.

## Safety boundary

ForgeOps requires an explicit kubeconfig file and the exact context `kubernetes-admin@kubernetes`. It stops before resource collection if either preflight fails.

The collector can run only its built-in read operations for:

- Kubernetes client and server versions;
- the four expected Nodes;
- five named Deployments and only their fixed Pod selectors;
- four named Services through their EndpointSlices; and
- `v1beta1.metrics.k8s.io` APIService availability.

It does not collect logs, Events, Secrets, ConfigMaps, environment values, addresses, complete Kubernetes objects, arbitrary resources, or broad namespace state. It cannot apply, create, delete, patch, scale, restart, execute in, or port-forward to a workload.

Optional HTTP checks run only when the operator supplies explicit base URLs. Redirects are disabled, response bodies are bounded, and unrecognized response fields are discarded.

## Install locally for operator use

From a clean repository checkout:

~~~powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install .
.\.venv\Scripts\forgeops.exe provenance
.\.venv\Scripts\forgeops.exe snapshot --help
.\.venv\Scripts\foundry-check.exe --help
~~~

The normal install exposes both repository commands without binding a shared
Python interpreter to an editable checkout. No package is published to a
registry.

For source development, use the repository-owned launcher:

~~~powershell
python .\scripts\run-forgeops-dev.py provenance
~~~

Do not use a global editable installation as the operator default. Before
relying on any command, require provenance status `OK` and confirm the expected
module path and Python executable. Provenance output contains local paths and
should be reviewed before sharing.

## Identify the explicit kubeconfig

Use the kubeconfig already configured for the operator workstation. Do not assume that `$HOME\.kube\config` exists, and do not paste kubeconfig contents into a report.

To inspect only the configured environment path and current context in PowerShell:

~~~powershell
$env:KUBECONFIG
kubectl config current-context
~~~

Resolve multiple `KUBECONFIG` entries deliberately. Pass one regular file to ForgeOps; the command never silently falls back to ambient configuration.

## Collect Kubernetes evidence

~~~powershell
forgeops snapshot `
  --kubeconfig $env:KUBECONFIG `
  --context kubernetes-admin@kubernetes
~~~

Equivalent module invocation:

~~~powershell
python -m forgeops snapshot `
  --kubeconfig $env:KUBECONFIG `
  --context kubernetes-admin@kubernetes
~~~

## Include explicit application checks

Use only URLs deliberately selected by the operator:

~~~powershell
forgeops snapshot `
  --kubeconfig $env:KUBECONFIG `
  --context kubernetes-admin@kubernetes `
  --restaurant-url http://192.168.243.112:30080 `
  --workbench-url http://192.168.243.112:30081
~~~

The Restaurant API allowlist is `/version`, `/health`, `/ready`, and `/status`. The Workbench allowlist is `/healthz`. Omitting a base URL skips that optional endpoint group; it does not manufacture a passing result.

## Render Markdown

Markdown contains the same ordered checks and status semantics as terminal output:

~~~powershell
forgeops snapshot `
  --kubeconfig $env:KUBECONFIG `
  --context kubernetes-admin@kubernetes `
  --format markdown > forgeops-snapshot.md
~~~

A redirected report is durable evidence. Review it before sharing. The renderer omits kubeconfig paths and contents, credentials, node and Pod addresses, HTTP headers, complete objects, labels, annotations, environment data, and volumes.

## Render deterministic JSON

JSON contains the same ordered evaluated checks, statuses, summary, overall result, and exit-code semantics as terminal and Markdown output:

~~~powershell
forgeops snapshot `
  --kubeconfig $env:KUBECONFIG `
  --context kubernetes-admin@kubernetes `
  --format json > forgeops-snapshot.json
~~~

The artifact identifies schema `forgeops.snapshot/v1alpha1` and includes the collection time, requested context, scope, redaction statement, summary, checks, and limitations. Optional `expected`, `observed`, and `errorCategory` fields appear only when applicable. It does not contain the collector's raw responses or restore fields discarded during normalization.

Serialization is deterministic for the same evaluated snapshot. Independent live runs are not byte-identical evidence because their collection timestamps and observed state can differ. Review a redirected JSON artifact before sharing it and retain it only according to the operator's chosen local evidence-handling practice.

## Validate a saved JSON artifact offline

Validate one explicitly selected regular file before passing it to a later consumer:

~~~powershell
forgeops evidence validate `
  --input .\forgeops-snapshot.json
~~~

The validator reads no more than 1 MiB and requires UTF-8 JSON without duplicate keys or non-standard numeric constants. It accepts only schema `forgeops.snapshot/v1alpha1` with the reviewed ordered fields, value types, UTC timestamps, unique check identifiers, scope, redaction statement, limitations, and internally consistent summary.

A successful result is concise and separates contract validity from contained health:

~~~text
VALID forgeops.snapshot/v1alpha1 checks=33 containedOverall=PASS containedExit=0
~~~

A valid artifact containing `WARN`, `FAIL`, or `UNKNOWN` also returns validator exit code `0` while reporting that contained status and exit code. Validator exit code `2` means that the input was unreadable, oversized, malformed, unsupported, or inconsistent. The validator never repairs or rewrites the file.

## Compare two saved artifacts offline

~~~powershell
forgeops evidence compare `
  --before .\forgeops-snapshot-before.json `
  --after .\forgeops-snapshot-after.json
~~~

Both files must independently pass the strict validator before any comparison is printed. The command reports check additions, removals, status transitions, and changes to the validated observation, source, expected, observed, or error-category fields. Results are ordered by check identifier. Collection timestamps are shown for operator context but are not classified as evidence changes.

Comparison exit codes are separate from the health status inside either artifact:

| Exit | Meaning |
| --- | --- |
| `0` | Both artifacts are valid and operationally equivalent after timestamps are ignored. |
| `1` | Both artifacts are valid and one or more checks differ. |
| `2` | An artifact is invalid, unavailable, or out of chronological order. |

An `after` timestamp may equal the `before` timestamp but must not be earlier. A reported change is not a diagnosis, causal claim, severity score, or recommendation. The command does not retain, rewrite, or copy either artifact and does not invoke kubectl, HTTP, or another network path.

### Render comparison JSON

Use the explicit JSON selector when a script or separately reviewed offline consumer needs the comparison:

~~~powershell
forgeops evidence compare `
  --before .\forgeops-snapshot-before.json `
  --after .\forgeops-snapshot-after.json `
  --format json
~~~

The output schema is `forgeops.comparison/v1alpha1`. It preserves the two collection timestamps, contained overall statuses, deterministic summary counts, comparison exit code, and ordered deltas. Each delta contains only its check identifier, classification, before/after status, and changed field names. Added and removed checks use explicit `null` for the absent status and an empty changed-field array.

The JSON does not include either artifact path, observation text, expected or observed values, evidence source, error text, or a copy of either artifact. Redirecting output to a file is an operator action; ForgeOps does not create, retain, reload, validate, sign, or establish provenance for comparison documents. Exit codes remain `0`, `1`, and `2` exactly as described above, including exit `1` after a complete valid JSON document is emitted for a difference.

Validation and comparison are offline. They do not read or search for a kubeconfig, invoke kubectl, make an HTTP request, discover another file, contact a network service, or mutate the cluster. Passing validation establishes contract compatibility and internal consistency only; it does not prove artifact provenance, cryptographic authenticity, cluster health, or the absence of sensitive text in arbitrary string values. Review the artifact before sharing it.

## Create and verify an exact-byte integrity record

Create a deterministic sidecar only after ForgeOps validates the evidence:

~~~powershell
forgeops evidence integrity create `
  --input .\forgeops-snapshot.json > .\forgeops-snapshot.integrity.json
~~~

The `forgeops.integrity/v1alpha1` document contains the evidence schema,
collection timestamp, context, algorithm, SHA-256 digest, exact byte length,
and limitation statement. It omits the input path and evidence values. ForgeOps
hashes the same bytes it validated and writes the record only to standard
output; choosing and protecting a destination remains an operator action.

Retain the record separately if it will serve as a trusted reference. Verify it
later with:

~~~powershell
forgeops evidence integrity verify `
  --input .\forgeops-snapshot.json `
  --record .\forgeops-snapshot.integrity.json
~~~

Integrity verification has its own exit semantics:

| Exit | Meaning |
| ---: | --- |
| `0` | The valid evidence bytes and bounded metadata match the valid record. |
| `1` | Both inputs are valid, but length, digest, or metadata differs. |
| `2` | The evidence or integrity record is invalid or unreadable. |

The evidence remains limited to 1 MiB and the integrity record to 64 KiB.
Verification reads only the two explicit files and emits no input path or
evidence content. A match detects alteration relative to a separately retained
trusted record. It does not identify the creator, authenticate either file,
provide trusted time, or prove chain of custody; replacing both files can still
produce a matching unsigned pair.

## Exercise the synthetic scenario corpus

Milestone 050 provides five focused examples under
`tests/fixtures/forgeops/scenarios`. They demonstrate timestamp-only stability, a
Pod-restart warning, a routing regression, incomplete evidence, and recovery. Each
directory contains `before.json`, `after.json`, and the exact
`expected-comparison.json`.

From one scenario directory:

~~~powershell
forgeops evidence validate --input .\before.json
forgeops evidence validate --input .\after.json
forgeops evidence compare --before .\before.json --after .\after.json
forgeops evidence compare `
  --before .\before.json `
  --after .\after.json `
  --format json
~~~

These are deliberately isolated synthetic checks, not captured SignalForge evidence
or complete snapshots. Their overall status applies only to the focused artifact. A
recovery still returns comparison exit `1` because the valid artifacts differ; that
exit is not a failed recovery or severity judgment.

Replay the three explicit files without directory discovery:

~~~powershell
forgeops scenario replay `
  --before .\before.json `
  --after .\after.json `
  --expected .\expected-comparison.json
~~~

The expected comparison is limited to 256 KiB and must pass the strict
`forgeops.comparison/v1alpha1` loader. Replay returns `0` when the actual
validated comparison exactly equals the validated expectation, `1` when valid
inputs differ from the expectation, and `2` for invalid evidence, expectation,
or chronology. The output omits file paths and evidence values.

Replay success is evaluation success, not health success. A routing regression,
incomplete-evidence transition, or recovery can correctly contain comparison
exit `1` while replay itself returns `0`. Replay does not automatically verify
Milestone 052 integrity records; use integrity verification separately when a
trusted sidecar exists.

## Interpret results

| Status | Meaning |
| --- | --- |
| `PASS` | The selected evidence matched its fixed expectation. |
| `WARN` | Evidence was complete, but a non-fatal concern such as a Pod restart was observed. |
| `FAIL` | Evidence was complete and did not match the fixed expectation. |
| `UNKNOWN` | Required evidence was missing, malformed, timed out, unauthorized, oversized, or otherwise incomplete. |

| Exit code | Meaning |
| ---: | --- |
| `0` | Every collected required check passed. |
| `1` | Collection completed with at least one warning or failure. |
| `2` | Invocation was invalid or required collection was incomplete. |

`UNKNOWN` takes precedence over an otherwise healthy-looking subset. A result is a point-in-time observation and does not replace Prometheus, Grafana, application-specific investigation, or operator judgment.

## Failure handling

- Invalid kubeconfig or context: correct the explicit input; do not broaden discovery.
- Timeout or authorization failure: retain the `UNKNOWN` result and investigate access separately.
- Missing or malformed object: compare the fixed target with the repository manifests before changing the collector.
- HTTP failure: verify the operator-provided base URL and private-lab reachability; ForgeOps will not discover an alternative address or follow a redirect.
- `FAIL` or `WARN`: use the existing operator runbooks to investigate. ForgeOps never applies a correction.

Do not respond to a failed snapshot by granting broader RBAC, reading restricted objects, or converting the command into a mutating workflow without a separately reviewed milestone.
