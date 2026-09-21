# Testing and validation

**Inventory date:** 2026-09-21

This document defines what The Foundry Initiative means when it reports tests
and validation results. It separates executable test cases, generated scenario
cases, static validators, build checks, and live acceptance so unlike evidence
is not collapsed into one misleading total.

## Current inventory

| Suite | Current count | Scope |
| --- | ---: | --- |
| ForgeOps Python tests | 178 | `tests/test_forgeops*.py`; included in both Python totals below |
| Top-level Python tests | 248 | Everything collected below `tests/` |
| Restaurant API Python tests | 9 | `apps/restaurant-api/tests/test_main.py` |
| Complete repository Python discovery | 257 | Top-level 248 plus Restaurant API 9 |
| Forge YAML Workbench Vitest tests | 92 | Seven `apps/forge-yaml-workbench/src/*.test.js` files; separate from Python totals |
| ForgeOps Console Go tests | 47 | Test functions across eight core packages; table subtests not added to this count; separate from Python totals |
| ForgeOps Console Vitest tests | 12 | API tests plus Pod diagnostics DOM lifecycle/rendering tests; separate from Python totals |
| Prometheus alert scenarios | 19 | Generated cases executed by pinned `promtool`; separate from Python totals |

The Python counts are nested, not additive: the 178 ForgeOps tests are part of
the 248 top-level tests, and the 248 plus the nine Restaurant API tests produce
the 257-test complete Python discovery. The browser, Go, and promtool
scenarios use different runners and must be reported separately rather than as
an artificial grand total.

A test count is the number of cases collected by its runner. It is not a count
of assertions or behaviors. One test may verify several invariants or iterate
over a reviewed scenario corpus. For example, one Milestone 061 test executes
all nine adversarial incident-brief cases.

## Console C3 live walkthrough evidence

On 2026-09-21, after explicit authorization, the operator built accepted source
`82741388f6b2c79a381ac35b6c7bf4e4ecbf90b5` on Windows and supplied terminal output
and browser screenshots for a bounded read-only SignalForge walkthrough.
The four Vitest API tests, browser production build, Go package tests, and Go
production binary build passed on the laptop. These are additional executions,
not new test cases; that walkthrough did not increase the inventory.

All six resource views, their displayed relationships, and explicit scope
reset/reselection were observed successfully. Namespace discovery supplied the
selection control. This manual happy-path evidence is separate from synthetic
demo checks and automated tests; it does not prove concurrent in-flight
cancellation, every security/error path, or application network reachability.
The [C3 milestone](milestones/forgeops-console-c3-read-only-resource-browser.md#live-read-only-walkthrough--2026-09-21)
records the observations, limits, and open scheduling-label follow-up. Screenshots
and kubeconfig contents are not committed as part of this reconciliation.

## Console C4 validation

C4 adds 16 Go test functions, eight Vitest cases, and four Python policy tests.
The 47 Go functions pass under the race detector, with `go vet`, formatting,
unchanged locked module graph after tidy, and both Go entry-point builds.
All 12 Vitest cases, TypeScript/Vite build, and production dependency audit
(zero vulnerabilities) pass. Top-level unittest passes 248 cases; full pytest
passes 257 using `PYTHONPATH=src:apps/restaurant-api` on Linux. Pytest reports an
existing Starlette/AnyIO deprecation warning; this is not a test failure.

New coverage includes diagnostic capability isolation, atomic namespace scope
selection, fixed typed GETs against a loopback test server, bounds, error
mapping, cancellation/deadline stream closure, stale generations, hostile text,
offline preview quoting, sensitive-data acknowledgement, and late UI responses.
The synthetic HTTP demo smoke passes bootstrap, log/Event reads, preview,
metadata-only activity, no-store headers, and stale-generation rejection.
These checks contact no live cluster. DOM tests do not establish real-browser
accessibility or Windows shell equivalence; previews are never executed.

See the [C4 contract and gate status](milestones/forgeops-console-c4-pod-diagnostics.md).

## What the suites cover

### ForgeOps

The focused ForgeOps suite covers:

- explicit kubeconfig, context, URL, command, timeout, size, and redaction
  boundaries;
- deterministic snapshot evaluation and text, Markdown, and JSON rendering;
- strict evidence, comparison, integrity, runbook-catalog, mapping, and
  incident-brief contracts;
- duplicate keys, invalid encodings, unsafe paths, field order, chronology,
  count recalculation, and cross-document consistency;
- comparison, scenario replay, brief replay, and their separate exit domains;
- exact-byte integrity without authenticity or chain-of-custody claims;
- grounded runbook mapping without cause, diagnosis, recommendation, or
  execution authority;
- deterministic incident states, uncertainty precedence, golden text/JSON
  output, and adversarial boundary cases; and
- v1 product identity, version and Python-range alignment, MIT metadata,
  package selection, bounded workflow permissions and assets, release-note
  boundaries, and clean candidate source staging; and
- offline isolation, including tests that prove collection or network runners
  are not constructed by offline commands.

The suite uses checked-in synthetic fixtures. Passing it does not establish
current cluster health, artifact authenticity, runbook applicability, incident
cause, or remediation authorization.

### Other Python tests

- `tests/test_checks.py` and `tests/test_cli.py` cover the earlier
  `foundry-check` repository inspector and its CLI exits and output contracts.
- `tests/test_alert_rules.py` covers alert-rule scope and negative regressions;
  it does not replace promtool rule evaluation.
- `tests/test_grafana*.py` covers Grafana manifest, storage, health, and probe
  boundaries.
- `tests/test_prometheus_alert_activation.py` covers explicit activation and
  rollback safeguards without activating anything.
- `tests/test_repository_security.py` covers explicit read-only workflow
  defaults, immutable trusted Action references, forbidden privileged pull
  request triggers, bounded write permission, complete Dependabot ecosystem
  coverage, separated security and patch-only version-update groups, the
  Restaurant API pytest security floor, private vulnerability-reporting
  guidance, the required validation/dependency-review gate, contribution
  templates, line-ending policy, and release-environment use by every
  publication job.
- `tests/test_forgeops_console_design.py` covers the C1 documentation contract:
  explicit local configuration, loopback-only intent, absent shell and mutation
  authority, strict brokered plugin capabilities, deferred third-party plugin
  loading, primary threat classes, preserved roadmap numbering, and ForgeOps v1
  independence.
- `tests/test_wiki_front_door.py` covers stable Wiki content, links, workflow
  triggers, and exact-copy publication behavior.
- `apps/restaurant-api/tests/test_main.py` covers root metadata, health,
  readiness, version, menu, status, analysis, metrics, and bounded
  unmatched-path metric labels.

### Forge YAML Workbench

The separate Vitest suite covers analyzer behavior, Kubernetes schema
validation, the pinned OWASP profile, formatting diffs, Markdown reports, Tree
search, and browser DOM interactions. Workbench CI also builds production
assets, checks strict-CSP compatibility, and audits locked dependencies. Those
build and audit steps are validation checks, not additional Vitest cases.

### Alert-rule scenarios

`scripts/export-alert-rule-tests.py` generates 19 independent expected-state
scenarios. Pinned Prometheus `promtool` 3.13.2 validates rule syntax and
evaluates those scenarios with no container network. These scenarios cover
healthy, partial, absent, stale, recovery, rollout, scoping, and timer behavior.
They are not live alert observations or notification-delivery tests.

## Running the suites

Run commands from the repository root unless a command changes directory.
Install the local package and the Restaurant API development requirements in an
isolated environment before running the complete Python discovery.

~~~powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install . `
  -r .\apps\restaurant-api\requirements.txt `
  -r .\apps\restaurant-api\requirements-dev.txt

$env:PYTHONPATH = "$PWD\src;$PWD\apps\restaurant-api"
.\.venv\Scripts\python.exe -m pytest -q
~~~

Useful narrower Python suites are:

~~~powershell
# Top-level Python suite: currently 248 tests
.\.venv\Scripts\python.exe -m pytest -q .\tests

# Focused ForgeOps suite: currently 178 tests
.\.venv\Scripts\python.exe -m unittest discover `
  -s tests -p 'test_forgeops*.py' -v

# Restaurant API suite: currently 9 tests
Push-Location .\apps\restaurant-api
..\..\.venv\Scripts\python.exe -m pytest -q
Pop-Location
~~~

Run the Workbench suite and its adjacent validation from its directory:

~~~powershell
Push-Location .\apps\forge-yaml-workbench
npm ci
npm test
npm run build
npm run csp:check
npm audit
Pop-Location
~~~

Run the ForgeOps Console suites from their respective module directories:

~~~powershell
Push-Location .\apps\forgeops-console
go test ./...
go vet ./...
Push-Location .\web
npm ci
npm test
npm run build
npm audit --omit=dev --audit-level=high
Pop-Location
Pop-Location
~~~

For Workbench pull requests, the Docker workflow also builds and starts a
native AMD64 image under the deployment's read-only, non-root, no-added-
capability constraints. It requires `/healthz` and `/` to respond and verifies
the page title plus the CSP, content-type, frame, and referrer security headers
before the existing AMD64 and ARM64 build validation runs.

Run the repository validators separately:

~~~powershell
python .\scripts\validate-k8s-manifests.py
python .\scripts\validate-wiki-front-door.py
python .\scripts\validate-alert-rules.py
python -m unittest tests.test_repository_security -v
git diff --check
~~~

Run actual alert-rule evaluation only with the pinned tool or the dedicated CI
workflow:

~~~powershell
python .\scripts\test-alert-rules.py `
  --promtool "C:\path\to\promtool.exe"
~~~

The GitHub Actions workflows remain the executable source of truth for CI
environment setup and path triggers:

- `.github/workflows/forgeops-ci.yml`
- `.github/workflows/forgeops-release.yml`
- `.github/workflows/restaurant-api-ci.yml`
- `.github/workflows/restaurant-api-docker.yml`
- `.github/workflows/forge-yaml-workbench-ci.yml`
- `.github/workflows/forge-yaml-workbench-docker.yml`
- `.github/workflows/k8s-manifest-validation.yml`
- `.github/workflows/alert-rule-validation.yml`
- `.github/workflows/repository-security-validation.yml`
- `.github/workflows/required-validation.yml`

## Evidence boundaries

These evidence types answer different questions:

| Evidence | What it establishes | What it does not establish |
| --- | --- | --- |
| Unit or integration test | Reviewed behavior matched an executable expectation | Current live-system health |
| Negative test | An invalid or forbidden case failed as expected | Absence of every possible failure |
| Golden-output test | Output exactly matched an accepted fixture | Truth or authenticity of arbitrary input |
| Synthetic replay | Production seams matched a reviewed scenario expectation | A live incident occurred |
| Static validator | Files satisfy repository-owned structural rules | Runtime behavior outside those rules |
| Build or dependency check | The reviewed source builds or passes the named audit | Deployment or live acceptance |
| Live acceptance | A bounded observation passed against an approved target | Authority beyond the observed scope or time |

Passing tests support a bounded engineering claim; they are not a substitute
for evidence appropriate to a different domain.

## Maintenance rule

Any change that adds, removes, parameterizes, relocates, or changes discovery
of tests must update this guide in the same pull request when it changes a
reported count or suite boundary. The pull request and milestone evidence must
name the affected suite rather than report an unlabeled total.

When updating counts:

1. collect the focused suite and the complete discovery independently;
2. record the date and exact command scope;
3. keep nested counts visibly nested rather than adding them twice;
4. keep Vitest cases, promtool scenarios, validators, builds, audits, and live
   acceptance in their own categories; and
5. explain any surprising delta, such as the nine Restaurant API tests that
   distinguish the 248-test top-level suite from the 257-test complete Python
   discovery.

Historical milestone counts remain historical evidence and must not be edited
to match later suite growth.
