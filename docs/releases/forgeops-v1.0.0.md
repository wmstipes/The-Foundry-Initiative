# ForgeOps v1.0.0

ForgeOps v1.0.0 is the first supported deterministic incident-copilot release
for the SignalForge lab.

## Included

- bounded read-only SignalForge snapshots from an explicit kubeconfig and exact
  context;
- deterministic text, Markdown, and JSON evidence;
- strict offline evidence, comparison, integrity, mapping, and brief contracts;
- five synthetic scenarios with exact comparison and incident-brief replay;
- validated runbook knowledge and deterministic catalog-rule mapping;
- deterministic structured and operator-facing incident briefs; and
- explicit execution provenance and separate exit domains.

## Install

Download both release assets, verify the wheel against `SHA256SUMS.txt`, and
install the wheel into a fresh isolated Python 3.11–3.14 environment with
`--no-index`. Follow the
[ForgeOps release guide](https://github.com/wmstipes/The-Foundry-Initiative/blob/forgeops-v1.0.0/docs/guides/forgeops-release.md) for exact PowerShell
commands and rollback.

## Boundaries

ForgeOps does not establish current health beyond supplied point-in-time
evidence, infer cause or severity, recommend remediation, authorize a runbook,
or mutate a cluster. It includes no model, retrieval service, background
service, runtime dependency, PyPI publication, container image, or deployment.

The `v1alpha1` artifact schema names remain intentional. Package v1 does not
declare those schemas to be stable v1 APIs.
