# ForgeOps read-only snapshot runbook

This runbook operates the local ForgeOps snapshot command introduced in Milestone 045. The command collects a bounded point-in-time view of named SignalForge resources. It is not continuous monitoring, a complete cluster-health claim, a compliance check, or a remediation tool.

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

## Install locally

From a clean repository checkout:

~~~powershell
python -m pip install -e .
forgeops snapshot --help
foundry-check --help
~~~

The editable install exposes both repository commands. Milestone 045 does not publish a package to a registry.

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
