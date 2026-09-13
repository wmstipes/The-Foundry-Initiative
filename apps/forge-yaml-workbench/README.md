# Forge YAML Workbench

Forge YAML Workbench is a browser-based YAML inspector for the SignalForge lab. It parses YAML locally in the browser and offers Kubernetes-specific and General YAML inspection modes.

## Version 0.3.0 scope

- Paste, edit, open, format, and download YAML.
- Parse multi-document YAML files.
- Start in Kubernetes mode and explicitly switch to General YAML mode without changing the editor contents.
- Accept mapping, sequence, and scalar document roots in General YAML mode.
- Summarize each General YAML document by root type and shape while suppressing Kubernetes-only operational findings.
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

The Workbench performs YAML parsing in both modes and deterministic operational checks only in Kubernetes mode. General YAML mode does not infer Kubernetes semantics. The Workbench does not currently perform complete Kubernetes OpenAPI schema validation or contact the Kubernetes API server. A successful report does not prove that a Kubernetes manifest will be admitted or run successfully.

Browser-local Kubernetes schema validation is deferred to Milestone 036. Broader OWASP Kubernetes Top 10 coverage is deferred to Milestone 037.

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
