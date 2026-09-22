# Security policy

## Supported versions

The Foundry Initiative is a personal engineering and learning project. Security
maintenance applies to the current `main` branch and the most recent published
version of each component. Older images, packages, tags, and milestone states
are retained as historical evidence and are not maintained as supported
releases.

## Repository security controls

The repository uses GitHub-hosted controls together with tracked policy:

- Dependency graph, Dependabot alerts, security updates, grouped security
  updates, secret scanning, push protection, and private vulnerability
  reporting are enabled.
- Dependabot checks GitHub Actions, Python, Go modules, npm, and Docker dependencies on a
  weekly schedule. Security updates are separated from patch-only version
  groups so higher-risk minor and major upgrades can be reviewed individually.
- Trusted reusable GitHub Actions are pinned to full commit SHAs, workflows
  declare read-only repository contents by default, and privileged
  `pull_request_target` execution is forbidden.
- The active `Protect main` ruleset requires pull requests and resolved review
  conversations, blocks branch deletion and non-fast-forward updates, and has
  no bypass actors. Because this is a single-maintainer project, it does not
  require an approving review count.
- Merges require the always-running `Gate 4 required validation` status check,
  which covers complete Python discovery, Workbench tests/build/audit,
  repository and manifest validators, and dependency review. CodeQL must
  report no errors and no security alert at high severity or above.
- Published GitHub releases are immutable. Release-tag rules block updates,
  deletion, and force pushes for ForgeOps, Workbench, and Restaurant API tags.
  Publication jobs use the deployment-scoped `release` environment.

`tests/test_repository_security.py` validates the security policy represented
by tracked repository files. It cannot prove GitHub-hosted settings such as
secret scanning, push protection, or ruleset enforcement; those settings must
also be reviewed in the repository's GitHub configuration.

## Reporting a vulnerability

Use GitHub's [private vulnerability reporting](https://github.com/wmstipes/The-Foundry-Initiative/security/advisories/new)
for suspected vulnerabilities in ForgeOps, the Restaurant API, Forge YAML
Workbench, Kubernetes manifests, automation, or release workflows.

Please do not open a public issue for an undisclosed vulnerability and do not
include credentials, tokens, private keys, personal data, or exploit material
in a public issue, discussion, or pull request.

A useful report includes:

- the affected component and version or commit;
- the conditions required to reproduce the issue;
- the observed and expected behavior;
- the likely security impact; and
- a minimal proof of concept when it can be shared safely.

Reports are reviewed on a best-effort basis. This personal project does not
promise a fixed response or remediation service level. Confirmed issues will be
handled through a private advisory until a fix and coordinated disclosure are
appropriate.

## Scope boundaries

Availability of the private SignalForge lab, intentionally local NodePort
access, unsupported historical versions, and findings that require already
authorized administrative access without crossing another security boundary
are normally outside the vulnerability-reporting scope. Configuration or
workflow behavior that could expose credentials, publish unintended artifacts,
weaken declared isolation, or permit unauthorized changes remains in scope.
