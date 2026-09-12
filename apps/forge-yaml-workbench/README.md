# Forge YAML Workbench

Forge YAML Workbench is a browser-based Kubernetes manifest inspector for the SignalForge lab. It parses YAML in the browser and presents important Kubernetes fields in a human-readable report.

## Version 0.1.2 scope

- Paste, edit, open, format, and download YAML.
- Parse multi-document YAML files.
- Display resource identity, namespace, labels, selectors, replicas, Services, containers, images, tags or digests, ports, probes, resources, volumes, and ServiceAccount use.
- Show an expandable object tree.
- Detect YAML parser errors and duplicate keys.
- Surface bounded operational findings such as mutable image tags, missing probes or resources, privileged containers, root execution, HostPath use, and automatic ServiceAccount-token mounting.
- Perform analysis in the browser without sending YAML to another service.

## Milestone 033 usability improvements

The `0.1.2` release keeps the same browser-local trust boundary while improving interaction precision:

- explicit feedback when formatting changes YAML or the input is already normalized
- parser diagnostics with clickable line and column locations
- preservation of an opened YAML filename when downloading
- keyboard shortcuts for opening, formatting, and downloading
- confirmation before clearing unsaved edits
- DOM interaction coverage alongside the analyzer tests

## Milestone 034 deterministic checks

The current source branch deepens the bounded operational review with:

- clickable YAML paths, plain-language explanations, and suggested corrections for every operational finding
- workload selector and Pod-template label consistency checks
- duplicate resource identity detection across multi-document input
- Service selector and named target-port checks against workloads included in the same file
- host PID and IPC namespace findings
- explicit container checks for privilege escalation, writable root filesystems, Linux capabilities, and non-root execution
- expandable fix guidance with copyable YAML examples and operational cautions
- initial OWASP Kubernetes Top 10:2025 K01 mapping, including an explicit RuntimeDefault seccomp check
- parsed-document and finding counts that avoid implying API-server validity

These checks are deterministic and browser-local. They do not replace Kubernetes OpenAPI validation, admission control, or server-side dry-run.

The OWASP references identify which security guidance informed a finding; they are not a claim that the Workbench performs a complete OWASP compliance assessment. Broader OWASP Kubernetes Top 10:2025 coverage is planned as a separate milestone.

## Validation boundary

The Workbench performs YAML parsing and deterministic operational checks. It does not currently perform complete Kubernetes OpenAPI schema validation or contact the Kubernetes API server. A successful report does not prove that a manifest will be admitted or run successfully.

Before deployment, continue to use repository validation and Kubernetes server-side dry-run.

## Local development

The first installation creates the repository lockfile:

~~~powershell
npm.cmd install
npm.cmd test
npm.cmd run build
~~~

Subsequent clean installations use `npm.cmd ci`.

## Container

The production container compiles the static application and serves it on port `8080` with an unprivileged NGINX runtime. The Dockerfile requires the generated `package-lock.json`, which must be committed before container CI is enabled.
