# Security policy

## Supported versions

The Foundry Initiative is a personal engineering and learning project. Security
maintenance applies to the current `main` branch and the most recent published
version of each component. Older images, packages, tags, and milestone states
are retained as historical evidence and are not maintained as supported
releases.

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
