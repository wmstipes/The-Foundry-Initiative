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
  weekly schedule. Security updates are separated from version-update groups.
  Version groups are patch-only except for the Console's `k8s.io/api`,
  `k8s.io/apimachinery`, and `k8s.io/client-go`: these coupled libraries share
  one group for all version-update types to avoid incompatible mixed releases.
  Other minor and major upgrades remain individually reviewed. Grouping does
  not enable automatic merging.
- Trusted reusable GitHub Actions are pinned to full commit SHAs, workflows
  declare read-only repository contents by default, and privileged
  `pull_request_target` execution is forbidden.
- The active `Protect main` ruleset requires pull requests and resolved review
  conversations, blocks branch deletion and non-fast-forward updates, and has
  no bypass actors. Because this is a single-maintainer project, it does not
  require an approving review count.
- Merges require the always-running `Gate 4 required validation` status check,
  which covers complete Python discovery, Workbench tests/build/audit,
  native Linux/Windows Console tests/build/installed verification,
  repository and manifest validators, and dependency review. PRs require
  dependency-review success; only non-PR events may skip it. CodeQL must
  report no errors and no security alert at high severity or above.
- New GitHub releases use immutable publication. The September 19, 2026
  `forgeops-v1.0.0` release predates that protection and remains mutable;
  its tag is protected, but its attached assets are a documented legacy
  exception. The September 22 Console preview is immutable. See the
  [October security record](docs/security/review-2026-10-01.md) for asset hashes,
  evidence limits, and administrative controls still awaiting verification.
  Release-tag rules block updates,
  deletion, and force pushes for ForgeOps, ForgeOps Console, Workbench, and
  Restaurant API tags.
  GitHub Actions publication jobs use the deployment-scoped `release`
  environment. Publication preflight requires the exact commit to have passed
  the main-push Required Validation workflow and its Gate 4 job. Manual
  publication requires `main` and an explicit matching source SHA; versioned
  container publication rejects existing tags and API uncertainty. All
  publication jobs are serialized. These checks do not replace GitHub
  environment/ref restrictions or registry-enforced immutability.
  The Console preview was published manually through the reviewed
  [exact-asset procedure](docs/releases/forgeops-console-v0.1.0-rc.1-publish.md),
  which verifies draft downloads before publication; that CLI operation is not
  governed by an Actions environment approval. Release immutability still applies.

`tests/test_repository_security.py` validates the security policy represented
by tracked repository files. It cannot prove GitHub-hosted settings such as
secret scanning, push protection, or ruleset enforcement; those settings must
also be reviewed in the repository's GitHub configuration.

## Reporting a vulnerability

Use GitHub's [private vulnerability reporting](https://github.com/wmstipes/The-Foundry-Initiative/security/advisories/new)
for suspected vulnerabilities in ForgeOps, ForgeOps Console, the Restaurant API, Forge YAML
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
