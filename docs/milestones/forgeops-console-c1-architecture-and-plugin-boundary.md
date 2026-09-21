# ForgeOps Console C1 — architecture and plugin boundary

## Purpose

C1 admits ForgeOps Console as a parallel Project Forge workstream because a
local visual inspection and evidence-selection workflow can directly improve
the final incident-copilot demonstration. It also establishes trust boundaries
before application code or Kubernetes access exists.

## Accepted outcome

C1 defines:

- a local browser application backed by a loopback-only Go core;
- explicit kubeconfig and context selection without ambient fallback;
- typed Kubernetes API operations rather than arbitrary shell execution;
- a read-only v0.1 resource and operation allowlist;
- a versioned first-party plugin manifest, SDK, contribution, and capability
  model;
- credential, wrong-context, excessive-authority, plugin, browser, untrusted-
  data, command-confusion, and evidence-overclaim protections; and
- a separately gated C2-C7 implementation and release roadmap.

## Explicit exclusions

C1 adds no application code, package dependency, image, manifest, workload,
ServiceAccount, RBAC object, credential, live-cluster request, tag, release, or
deployment. It does not alter the ForgeOps v1.0.0 package, schemas, tag, assets,
or authority.

## Acceptance evidence

- Product architecture: `docs/design/forgeops-console-architecture.md`
- Threat model: `docs/design/forgeops-console-threat-model.md`
- Plugin contract: `docs/design/forgeops-console-plugin-contract.md`
- Workstream roadmap: `docs/roadmaps/forgeops-console-roadmap.md`
- Policy tests: `tests/test_forgeops_console_design.py`

The final local candidate passed:

- 238 complete Python tests, including eight C1 design-policy tests;
- 92 Forge YAML Workbench tests, production build, strict-CSP check, and locked
  dependency audit with zero reported vulnerabilities;
- Kubernetes manifest, Wiki front-door, Prometheus alert, and repository-
  security validators; and
- Python compilation and whitespace validation.

This evidence validates the repository candidate and documented policy. It
does not validate an application runtime, kubeconfig parser, Kubernetes client,
plugin loader, or live cluster connection because none exists in C1.

## Gate status

1. Planning and admission — approved by Mike.
2. Documentation implementation — complete on
   `codex/forgeops-console-c1`.
3. Validation — complete against the final local candidate.
4. Review PR — pending final candidate.
5. Merge and reconciliation — pending review and merge.
6. C2 admission — intentionally separate; C1 approval does not authorize code.
