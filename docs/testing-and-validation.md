# Testing and validation

**Inventory date:** 2026-09-20

This document defines what The Foundry Initiative means when it reports tests
and validation results. It separates executable test cases, generated scenario
cases, static validators, build checks, and live acceptance so unlike evidence
is not collapsed into one misleading total.

## Current inventory

| Suite | Current count | Scope |
| --- | ---: | --- |
| ForgeOps Python tests | 151 | `tests/test_forgeops*.py`; included in both Python totals below |
| Top-level Python tests | 215 | Everything collected below `tests/` |
| Restaurant API Python tests | 5 | `apps/restaurant-api/tests/test_main.py` |
| Complete repository Python discovery | 220 | Top-level 215 plus Restaurant API 5 |
| Forge YAML Workbench Vitest tests | 92 | Seven `apps/forge-yaml-workbench/src/*.test.js` files; separate from Python totals |
| Prometheus alert scenarios | 19 | Generated cases executed by pinned `promtool`; separate from Python totals |

The Python counts are nested, not additive: the 151 ForgeOps tests are part of
the 215 top-level tests, and the 215 plus the five Restaurant API tests produce
the 220-test complete Python discovery. The Workbench tests and promtool
scenarios use different runners and must be reported separately rather than as
an artificial grand total.

A test count is the number of cases collected by its runner. It is not a count
of assertions or behaviors. One test may verify several invariants or iterate
over a reviewed scenario corpus. For example, one Milestone 061 test executes
all nine adversarial incident-brief cases.

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
  coverage, and private vulnerability-reporting guidance.
- `tests/test_wiki_front_door.py` covers stable Wiki content, links, workflow
  triggers, and exact-copy publication behavior.
- `apps/restaurant-api/tests/test_main.py` covers health, version, analysis,
  metrics, and bounded unmatched-path metric labels.

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
# Top-level Python suite: currently 215 tests
.\.venv\Scripts\python.exe -m pytest -q .\tests

# Focused ForgeOps suite: currently 151 tests
.\.venv\Scripts\python.exe -m unittest discover `
  -s tests -p 'test_forgeops*.py' -v

# Restaurant API suite: currently 5 tests
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
5. explain any surprising delta, such as the five Restaurant API tests that
   distinguish the 215-test top-level suite from the 220-test complete Python
   discovery.

Historical milestone counts remain historical evidence and must not be edited
to match later suite growth.
