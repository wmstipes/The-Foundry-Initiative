# Testing and validation

**Inventory date:** 2026-09-23

This document defines what The Foundry Initiative means when it reports tests
and validation results. It separates executable test cases, generated scenario
cases, static validators, build checks, and live acceptance so unlike evidence
is not collapsed into one misleading total.

## Current inventory

| Suite | Current count | Scope |
| --- | ---: | --- |
| ForgeOps Python tests | 184 | `tests/test_forgeops*.py`; included in both Python totals below |
| Top-level Python tests | 254 | Everything collected below `tests/` |
| Restaurant API Python tests | 9 | `apps/restaurant-api/tests/test_main.py` |
| Complete repository Python discovery | 263 | Top-level 254 plus Restaurant API 9 |
| Forge YAML Workbench Vitest tests | 92 | Seven `apps/forge-yaml-workbench/src/*.test.js` files; separate from Python totals |
| ForgeOps Console Go tests | 61 | Test functions across core and demo packages; table subtests not added to this count; separate from Python totals |
| ForgeOps Console Vitest tests | 21 | API, App resource-transition, and Pod diagnostics DOM lifecycle/rendering tests; separate from Python totals |
| Prometheus alert scenarios | 19 | Generated cases executed by pinned `promtool`; separate from Python totals |

The Python counts are nested, not additive: the 184 ForgeOps tests are part of
the 254 top-level tests, and the 254 plus the nine Restaurant API tests produce
the 263-test complete Python discovery. The browser, Go, and promtool
scenarios use different runners and must be reported separately rather than as
an artificial grand total.

A test count is the number of cases collected by its runner. It is not a count
of assertions or behaviors. One test may verify several invariants or iterate
over a reviewed scenario corpus. For example, one Milestone 061 test executes
all nine adversarial incident-brief cases.

## Istio learning lab validation

The persistent lab adds live acceptance evidence, not a new automated test
count. The isolated namespace has three meshed Pods at 2/2 Ready, a stable v1
route and a healthy 50/50 canary route. Twenty manual canary calls yielded
11 v1 and nine v2 responses; that sample demonstrates both subsets, not an
exact long-term split. The client loop sends one request to `/` every 15
seconds; Prometheus measured eight HTTP 200 requests over a two-minute window
after rollout. The three lab proxy scrapes and three Restaurant API scrapes
were up, and the two Restaurant alerts remained healthy and inactive.
Grafana showed live traffic for both versions, HTTP 200 client responses, and
healthy proxy scrapes. The 503 panel had no current series after client proxy
replacement and no new injected fault; absence of that series is not proof
that a later fault or application error cannot occur. The lab does not test
production service routing, mTLS policy, network isolation, or Console mesh
inspection. See the [runbook](../k8s/istio-lab/README.md) for the reset path
and [PR #139](https://github.com/wmstipes/The-Foundry-Initiative/pull/139)
for the reviewed change and live acceptance record.

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

Separately, the operator validated merged source `7910f0a` on Windows: 12 Vitest
cases, all Go package tests, web production build, and production Go binary
build passed; `npm.cmd ci` reported zero vulnerabilities. This was not a Windows
race-detector run. These are repeat executions, not additional test cases.

The authorized SignalForge walkthrough on 2026-09-21 observed one current
container log snapshot with an incompleteness warning, no matching Pod Events,
PowerShell/POSIX previews for logs and Events (not executed), and successful
clear and scope-reset behavior. The operator confirmed shutdown. The precise
log limit triggering the warning was not determined; an empty Event result is
not proof no Events occurred. No previous-instance read, live in-flight
cancellation, hostile-data injection, or exhaustive error/security testing was
performed. No raw logs, screenshots, or credentials are committed.

See the [C4 contract and gate status](milestones/forgeops-console-c4-pod-diagnostics.md).

## Console C5 boundary design validation

C5 adds documentation, not feature tests. All 248 existing top-level unittest
cases pass; suite counts above remain unchanged. The offline source-launcher
rehearsal at `da9acdd` validates before/after evidence and runbook mappings for
routing-regression, incomplete-evidence, routing-recovery, and stable-baseline.
Comparison and incident replay match each checked-in expectation, and text
briefs match exactly. This is repeated execution of existing behavior, not
four new tests or operator acceptance.

Relative-link targets and whitespace are checked for the changed documentation.
The [operator exercise](guides/forgeops-console-c5-operator-exercise.md) records
actual feedback separately from unperformed comparative checks. The
[candidate contract](design/forgeops-console-observation-contract.md) lists
future hostile-input, disclosure, lifecycle, and compatibility acceptance.
All four exercise prompts now have conversational operator feedback; no new
Console fixture run, comparative timing, or release-identity verification was
performed by that discussion.
No export implementation, candidate validator, new consumer, live access, or
fault injection was tested or delivered. PR checks and merge remain separate
from these local results.

## Console C6 local validation

C6 adds seven Go test functions (54 total) and seven Vitest cases (19 total).
Table subcases are not added to the Go function count. Python inventory stays
unchanged: all 248 top-level unittest cases pass, including the 27 Console
policy checks. No new documentation-string policy tests were added.

The Go package tests pass with the race detector; Go vet and formatting pass.
Browser tests, TypeScript/Vite
build, production dependency audit (zero reported vulnerabilities), and both
Go executable builds pass. `go mod tidy` leaves go.mod/go.sum unchanged.

The new tests exercise supporting-list pagination and relationship clipping on
list and read, late cancellation, failed context discovery, stale browser rows,
wrong-context responses, unmount cancellation, diagnostic panic activity and
sanitization, missing handlers/contributions, permanent session close, joined
shutdown and its deadline, and mismatched source identity. These are synthetic
checks; they do not prove arbitrary-code isolation or live failure behavior.

The standalone `scripts/verify-forgeops-console-bundle.py` rehearsal passes a
matching built demo/browser pair, rejects a mismatched source fingerprint before
startup, then restarts the valid pair and verifies bounded shutdown. It compares
Go and Vite identities and exercises only synthetic namespace/resource reads.
This integration check is also added to the existing Console browser CI job.
It is one standalone rehearsal, not an additional unittest or Vitest case.

The source fingerprint establishes matched inputs, not signed provenance or
compiled-byte authenticity. These initial local checks did not establish live
cluster, EKS, Windows runtime, historical-release rollback, or C5 export
acceptance. PR #108 subsequently merged with passing PR checks.

On 2026-09-22, the operator verified the merged revision on Windows: all 19
Vitest cases, frontend build, production executable build, and synthetic-demo
build/startup/browser transitions/Ctrl+C shutdown passed. The Go suite remained
incomplete: Application Control blocked `internal/resources` test execution
(event 3077), while other packages passed, some from cache. Smart App Control
was On. This is a launch block, not a failed assertion or a passing resources
suite. No additional tests or inventory changes result from this closeout.
Full Windows support requires resolving the execution block and running that
suite; the demo does not establish live or historical-release acceptance.
See the [operator closeout record](milestones/forgeops-console-c6-plugin-compatibility-planning.md#bounded-closeout--2026-09-22). See the [C6 implementation and limits](design/forgeops-console-c6-compatibility-lifecycle.md).

## Console C7 candidate validation

Six new `tests/test_forgeops_console_candidate.py` tests cover accepted extraction,
wrong outer digest, changed payload bytes, unsafe paths/symlinks, undeclared or
case-colliding members, and missing required runtime files. The top-level Python
inventory is now 254; complete discovery is 263 including Restaurant API's nine.
One Go regression test covers the actual Node cordon flag for both boolean
values, bringing the Go function inventory to 55. Browser tests remain 19 cases.

The required Console jobs now run natively on Linux and Windows. Browser CI
builds a committed-source archive and checks its extracted executables outside
the checkout: metadata, synthetic reads, production synthetic-only bootstrap,
configuration/Host/Origin/nonce denial, mismatch rejection and whole-pair
restoration. This is one integration rehearsal per platform, not additional
unittest or Vitest cases. Windows cleanup is forced and does not test Ctrl+C.
After a post-merge Windows connection reset, denial probes use an explicit
bodyless activity POST, close error responses, and repeat each boundary check
three times. Every probe still requires HTTP 403; transport failures remain
failures and now name the affected boundary. Test inventory is unchanged.
Candidate artifacts are unsigned, retained for 14 days, and cannot publish a
release. A passing hosted Windows runner does not resolve the laptop's Smart
App Control block or prove public OS/Kubernetes support.

See the [C7 gate record](milestones/forgeops-console-c7-release-readiness.md)
for exact-archive operator acceptance and publication verification. The automated
rehearsal contacts no live cluster. Separately, the operator accepted the same
Windows package with bounded SignalForge namespace/Pod/Service reads, clearing
old selection and Ctrl+C. Edge keyboard/focus, 200% zoom/narrow-window and three
focused Narrator areas passed. These observations add no automated test cases
and establish no broad compatibility or accessibility conformance.

The accepted Windows archive was subsequently published unchanged as
`forgeops-console-v0.1.0-rc.1`; GitHub's reported asset digest matches the recorded
operator hash. Linux has native CI evidence but no binary in this first preview.
Historical-release rollback is not applicable to this first Console release;
same-pair restoration remains the actual automated evidence. The earlier local
Go test-execution block remains disclosed and does not invalidate the accepted
packaged runtime.

## Console C5 aligned synthetic exercise validation

The later source demo adds explicit `routing-before` and `routing-after`
selections without changing the published Console prerelease. Two new Go test
functions (57 total in this source tree; C7 previously recorded 55) compare the
constructed slice's namespace, Service label and exact ready/not-ready/unknown
counts with each checked-in routing-regression snapshot, then check the actual
Console resource projection and reject an unsupported scenario. These tests
are fake-client/offline checks, not operator exercise results, live evidence,
installed-archive acceptance or a claim that Console captured ForgeOps
snapshots. The default demo and ForgeOps v1.0.0 contracts remain separate.

With freshly built browser assets, an offline loopback HTTP rehearsal started
each source demo mode separately, verified the synthetic bootstrap/context,
followed context activation and namespace discovery/selection, and read the
EndpointSlice through the resource route. It observed `3/3 ready` before and
`2/3 ready` after. The first harness attempt skipped namespace discovery and
was correctly denied; the corrected browser-order request sequence passed.
No browser interaction or operator timing was measured by this API rehearsal.

The [identity source design](design/forgeops-brief-release-identity-sources.md)
introduces no brief fields or new validator, and its release dates and digests
are not exercised by the synthetic demo. Record separate operator steps and
comparative evidence before claiming improved investigation or admitting an
exporter.

The follow-up source-only EndpointSlice triage path adds two Go test functions
(59 total) for bounded Pod target/condition projection, missing Pod transition
time, and a cross-namespace reference that must not become a link. The aligned
demo assertion verifies that its changed endpoint targets the third Pod. One
browser interaction case (20 Vitest cases total) checks that the target opens
an exact Pod read and reveals diagnostics. These are offline fake-client and
DOM checks; the published Windows preview has not changed, and the path awaits
operator acceptance. The Pod Ready transition is not an outage timestamp.

The agent review follow-up adds two diagnostics Go test functions (61 total)
and one browser case (21 total). The tests cover an endpoint with unset ready
status, Pod target UID projection, a replaced Pod during drilldown, and a
replacement during log retrieval. Existing diagnostics may still be read by
name when target UID is absent, with the limitation shown in the UI. The
post-read identity check bounds the log race but does not create durable
historical logging or prove an outage time.

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
# Top-level Python suite: currently 254 tests
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
   distinguish the 254-test top-level suite from the 263-test complete Python
   discovery.

Historical milestone counts remain historical evidence and must not be edited
to match later suite growth.
