# The Foundry Initiative

The Foundry Initiative is a personal engineering, learning, and portfolio-building project focused on rebuilding confidence through deliberate practice, useful systems, and visible progress.

This repository is a practical workspace for turning hands-on technical work into evidence of capability across:

* DevOps and platform engineering
* Kubernetes and cloud-native systems
* applied AI and machine learning experiments
* infrastructure automation and observability
* architecture notes and technical decision records
* structured learning plans and project milestones
* small, finishable projects that demonstrate growth over time

## Guiding principle

Progress does not need to be dramatic to be real.

The goal is to keep building, documenting, learning, and turning experience into evidence.

## Current focus

The active workstream is **SignalForge**, a Raspberry Pi Kubernetes lab designed to build practical experience with Kubernetes, containerized applications, infrastructure troubleshooting, deterministic incident analysis, and carefully gated future assistance.

SignalForge uses a restaurant analogy to make Kubernetes concepts easier to understand:

* a container image is a packaged kitchen
* a Pod is a running kitchen station
* a Deployment is the manager keeping enough stations running
* a Service is the stable phone number
* a ConfigMap is the local settings sheet
* NodePort is the public front door
* ForgeOps is the evidence-bound operations analyst; the human operator retains
  diagnosis and remediation authority

The cluster currently hosts the **SignalForge Restaurant API**, a FastAPI service, and **Forge YAML Workbench**, a browser-local YAML inspector with Kubernetes and General YAML modes.

## SignalForge Restaurant API

The SignalForge Restaurant API is the first Kubernetes-hosted application in this project.

It currently includes:

* FastAPI application
* Docker image built for `linux/arm64`
* Kubernetes Deployment
* Kubernetes Service
* ConfigMap-driven runtime settings
* health and readiness endpoints
* version, menu, and status endpoints
* rules-based `POST /analyze` troubleshooting endpoint
* NodePort access for laptop-based testing
* FastAPI Swagger UI access through `/docs`
* Prometheus-format application metrics through `/metrics`
* lightweight in-cluster Prometheus manifests with Pod-level discovery
* Kubernetes Metrics Server for current node and Pod CPU/memory visibility

**ForgeOps v1.0.0** is now the released deterministic incident copilot. It
collects a bounded read-only snapshot, validates and compares supplied evidence,
maps cataloged runbook references, and renders an artifact-bounded incident
brief. It does not infer cause, determine operational severity or impact,
recommend remediation, or authorize execution. Model and retrieval work remains
deferred until a demonstrated operator question cannot be answered by the
deterministic baseline.

## Forge YAML Workbench

Forge YAML Workbench is a browser-based YAML inspector deployed in the restricted `forge-tools` namespace. Kubernetes inspection is the default, with an explicit General YAML mode for mappings, sequences, and scalars. Both modes share browser-local parsing, formatting, diagnostics, file handling, searchable tree navigation, and review-first Markdown reports. Immutable release `0.10.0` is live with Milestone 042 safe browser-local YAML file drop. It has no Kubernetes API access or server-side storage and is available inside the private lab through NodePort `30081`.

Milestone 036 recovered from the rejected `0.4.0` browser startup defect without weakening the strict CSP. Milestone 037 added the pinned OWASP Kubernetes Top 10:2025 profile and corrected finding navigation. Milestone 038 deployed the explicit formatting-preview workflow as immutable `0.6.0`, Milestone 039 deployed review-first Markdown reports as immutable `0.7.0`, and Milestone 040 deployed counted Validation filters as immutable `0.8.0`. Milestone 041 keeps its Tree search index and navigation state ephemeral and inside the same browser-only trust boundary.

Milestone 042 adds one-file YAML drag-and-drop with visible and accessible target states, shared unsaved-change protection, deterministic state boundaries, and no upload or persistence path. Immutable `0.10.0` is published, digest-pinned, deployed, runtime-verified, live browser-accepted, and merged through PR #23 at `020d5e7`.

## ForgeOps snapshot

ForgeOps now has a local deterministic snapshot command. It checks a fixed allowlist of SignalForge Nodes, Deployments, selected Pods, EndpointSlices, and Metrics APIService availability. Optional Restaurant API and Workbench checks run only against explicit operator-provided URLs.

~~~powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install .
.\.venv\Scripts\forgeops.exe provenance
.\.venv\Scripts\forgeops.exe snapshot `
  --kubeconfig $env:KUBECONFIG `
  --context kubernetes-admin@kubernetes
~~~

The repository-local environment is the supported operator mode. For source
development, `scripts/run-forgeops-dev.py` explicitly selects the current
checkout rather than relying on a global editable installation. Always run
`forgeops provenance` first to see the loaded version, module path, Python
executable, execution mode, and recorded installation source.

ForgeOps v1 is packaged separately as `signalforge-forgeops`. The supported
public artifact is the wheel plus `SHA256SUMS.txt` on the
[ForgeOps v1.0.0 GitHub Release](https://github.com/wmstipes/The-Foundry-Initiative/releases/tag/forgeops-v1.0.0);
it is not published to PyPI. See the
[release guide](docs/guides/forgeops-release.md) for verification, isolated
offline installation, acceptance, and rollback.

Add `--format markdown` for a reviewable report or `--format json` for a deterministic machine-readable evidence artifact. Provide `--restaurant-url` and `--workbench-url` to include the five accepted application endpoints. All three renderers derive from the same evaluated snapshot and preserve the same ordered checks, status semantics, summary, and exit code. The command uses only bounded read operations, never falls back to an ambient kubeconfig or context, does not read sensitive Kubernetes objects, and cannot mutate the cluster. `UNKNOWN` evidence fails closed with exit code `2`.

Validate one explicitly selected saved artifact offline before passing it to another consumer:

~~~powershell
forgeops evidence validate --input .\forgeops-snapshot.json
~~~

Validation checks the supported schema, field order and types, timestamps, unique check identifiers, and summary consistency without invoking kubectl, making an HTTP request, or changing the artifact. Validation success means that the contract is valid, not that the contained health result is `PASS`.

Compare two validated artifacts offline:

~~~powershell
forgeops evidence compare `
  --before .\forgeops-snapshot-before.json `
  --after .\forgeops-snapshot-after.json
~~~

Comparison reports added, removed, status-changed, and evidence-changed checks in deterministic order. Exit code `0` means the valid artifacts are operationally equivalent after ignoring collection timestamps, `1` means they differ, and `2` means an input or its chronology is invalid. Comparison does not infer causes or recommendations.

Add `--format json` to emit the versioned `forgeops.comparison/v1alpha1` contract for an offline script or later bounded consumer. The JSON contains timestamps, contained overall statuses, deterministic counts, check identifiers, change classifications, before/after statuses, and changed field names. It does not reproduce artifact paths or underlying evidence values.

Milestone 050 adds a five-case synthetic scenario corpus for repeatable offline demonstrations of stable evidence, a Pod-restart warning, a routing regression, incomplete evidence, and recovery. Every scenario uses the existing evidence and comparison contracts and includes an exact expected comparison document. The corpus is synthetic evaluation data, not a live-health claim, training data, provenance record, diagnosis, or recommendation.

Replay one explicitly supplied scenario through the production validation and
comparison seams:

~~~powershell
forgeops scenario replay `
  --before .\before.json `
  --after .\after.json `
  --expected .\expected-comparison.json
~~~

Replay validates all three files, calculates the actual comparison, and checks
it against the expected comparison model. Replay exit `0` means the actual
deterministic result matched the expectation, even when that expected
comparison contains differences and comparison exit `1`. Replay exit `1` means
valid inputs produced a mismatch; exit `2` means an input or chronology is
invalid. It does not collect state, diagnose a cause, or recommend action.

Create a deterministic exact-byte integrity record for one validated artifact,
then retain that record separately if it will be used as a trusted reference:

~~~powershell
forgeops evidence integrity create `
  --input .\forgeops-snapshot.json > .\forgeops-snapshot.integrity.json

forgeops evidence integrity verify `
  --input .\forgeops-snapshot.json `
  --record .\forgeops-snapshot.integrity.json
~~~

The `forgeops.integrity/v1alpha1` record contains the evidence schema,
collection time, context, exact byte length, and SHA-256 digest. Verification
exit `0` means the validated artifact matches, `1` means it does not, and `2`
means an input is invalid. A matching digest detects byte alteration only when
the reference record was retained separately and trusted; it does not prove
who created the evidence, authenticate it, or establish chain of custody.

See the [ForgeOps operator and learning guide](docs/guides/forgeops-operator-learning-guide.md), [incident-copilot demonstration](docs/guides/forgeops-incident-copilot-demonstration.md), [ForgeOps snapshot runbook](docs/runbooks/forgeops-snapshot.md), [current architecture](docs/architecture.md), [project status](docs/project-status.md), and [Milestone 044-065 records](docs/milestones).

Validate the repository-owned runbook knowledge catalog offline:

~~~powershell
forgeops runbook catalog validate `
  --input .\docs\reference\forgeops-runbook-catalog.json
~~~

Map a validated comparison to the catalog without collection or diagnosis:

~~~powershell
forgeops runbook map `
  --comparison .\comparison.json `
  --catalog .\docs\reference\forgeops-runbook-catalog.json `
  --format text
~~~

Validate a saved mapping independently before using it as another offline
consumer's input:

~~~powershell
forgeops runbook mapping validate --input .\mapping.json
~~~

Validation success establishes contract validity, not mapping completeness,
catalog provenance, runbook applicability, or contained system health.

The [bounded incident-reasoning design](docs/design/forgeops-bounded-incident-reasoning.md)
defines evaluation and safety requirements for the deterministic JSON brief:

~~~powershell
forgeops incident brief `
  --comparison .\comparison.json `
  --mapping .\mapping.json `
  --format json
~~~

The command cross-checks both validated inputs and returns process exit `0`
when a brief is rendered, regardless of its bounded `STABLE`, `CHANGED`,
`DEGRADED`, `INCOMPLETE`, or `RECOVERED` state. No model integration exists.
Omit `--format` or select `--format text` for the deterministic operator-facing
view of the same facts and limitations.

Replay a brief against an explicit strict expectation:

~~~powershell
forgeops incident replay `
  --comparison .\comparison.json `
  --mapping .\mapping.json `
  --expected .\expected-incident-brief.json
~~~

Replay exit `0` means an exact deterministic match, not healthy contained state.

The [Milestone 061 readiness decision](docs/design/forgeops-model-readiness-decision.md)
defers model and retrieval integration. The approved
[Milestone 062 demonstration](docs/guides/forgeops-incident-copilot-demonstration.md)
now exercises deterministic briefing through separate synthetic-incident and
live read-only tracks. Probabilistic assistance must first show measurable
value over this baseline.

## Documentation front door

The [GitHub Wiki](https://github.com/wmstipes/The-Foundry-Initiative/wiki) is a curated reader-facing navigation layer. Repository documentation remains authoritative; the Wiki intentionally points to the current project status, architecture, roadmap, runbooks, milestone evidence, and vision instead of copying them.

The reviewed Wiki source lives in `docs/wiki`, and `scripts/validate-wiki-front-door.py` verifies its structure, links, stable-content boundary, and exact-copy publication contract.

The [testing and validation guide](docs/testing-and-validation.md) defines the
current suites, commands, dated counts, and the limits of each evidence type.

## Repository map

```text
The-Foundry-Initiative/
  apps/
    restaurant-api/        FastAPI application source, Dockerfile, and tests
    forge-yaml-workbench/  Browser-local YAML inspector, container, and tests

  k8s/
    fastapi-restaurant/    Kubernetes manifests for the Restaurant API
    prometheus/            Lightweight Prometheus manifests and scrape configuration
    metrics-server/        Kubernetes resource-metrics API manifests
    forge-yaml-workbench/  Restricted Workbench Namespace, Deployment, and Service

  docs/
    architecture.md        Current system architecture and constraints
    guides/                Consolidated current operator and learning guidance
    vision.md              Project purpose, principles, and direction
    learning-journal.md    Progress, lessons, and next small steps
    project-status.md      Current releases, milestones, and priorities
    testing-and-validation.md  Test suites, commands, counts, and evidence boundaries
    milestones/            Chronological implementation evidence
    observability/         PromQL baselines and observability guidance
    runbooks/              Operator procedures and recovery guidance
    wiki/                  Repository-owned source for the curated Wiki front door

  src/                      ForgeOps plus the legacy foundry-check source utility
  tests/                    Shared automated tests and offline ForgeOps fixtures
  experiments/              Prototypes and exploratory work

  ROADMAP.md                Project goals and future phases
  CONTRIBUTING.md           Working conventions for the project
```

## Current project status

The project has moved beyond the initial repository foundation phase and is now focused on the SignalForge Kubernetes learning lab.

Completed SignalForge milestones include:

* Raspberry Pi Kubernetes cluster online
* validation workload deployed successfully
* FastAPI Restaurant API deployed to Kubernetes
* Docker image built and deployed from Docker Hub
* rolling update performed
* rollback and roll-forward practiced
* runtime configuration moved into a ConfigMap
* first structured `/analyze` endpoint added
* NodePort access and external API testing confirmed
* Restaurant API testing and GitHub Actions CI added
* automated ARM64 Docker image publishing added
* versioned release `0.7.0` deployed
* Kubernetes manifests and validation stored in Git
* laptop-based `kubectl`, deployment, smoke-test, and operator helpers added
* operator runbook added
* Prometheus-format application metrics added at `/metrics`
* lightweight metrics-collection architecture selected
* lightweight Prometheus deployed with three healthy Pod-level targets
* request latency, traffic classification, and metric-cardinality protection added
* secure Kubernetes Metrics Server deployed with all four nodes available through `kubectl top`
* NVMe-backed Prometheus deployed with Pod-replacement persistence and isolated off-node backup/restore validation
* Grafana dashboards and bounded Prometheus rule evaluation deployed and recovery-tested
* Forge YAML Workbench `0.10.0` published for AMD64/ARM64, digest-pinned, deployed, and browser-validated with Kubernetes `v1.36.4` schema checks, General YAML mode, the pinned OWASP Kubernetes Top 10:2025 review profile, formatting preview, review-first Markdown reports, counted Validation filters, browser-local Tree search, and safe one-file YAML drop
* deterministic ForgeOps read-only snapshot implemented with offline fixtures, stable terminal, Markdown, and JSON output, a deny-by-default command runner, strict offline evidence validation, and deterministic offline comparison
* ForgeOps execution provenance and supported isolated operator/source-development modes
* exact-byte ForgeOps evidence-integrity records and bounded offline scenario replay
* validated runbook knowledge with deterministic grounded mapping and strict saved-mapping validation
* deterministic structured and operator incident briefs with exact replay and adversarial trust-boundary evaluation
* model and retrieval integration explicitly deferred until a read-only end-to-end demonstration identifies measurable operator value
* ForgeOps v1.0.0 published as a reproducible MIT-licensed wheel with SHA-256 checksums, Python 3.11-3.14 proof, and independent offline Windows acceptance

## Earlier utility: foundry-check

`foundry-check` is an earlier Python command-line utility in this repository.

It evaluates whether a local repository has a reasonable project foundation. It uses only the Python standard library at runtime and does not read secret contents.

The tool checks for baseline project structure, required documentation files, implementation and test directories, and suspicious tracked secret filenames.

It remains part of The Foundry Initiative as a small supporting utility and
early proof of practice. It is deliberately excluded from the
`signalforge-forgeops` v1 wheel and is not part of the supported ForgeOps
operator artifact.

## SignalForge development workflow

The current development workflow is:

1. Develop the FastAPI application locally.
2. Build and push a `linux/arm64` Docker image.
3. Deploy the image to the Raspberry Pi Kubernetes cluster.
4. Validate the application through Kubernetes Services.
5. Capture each meaningful step as a milestone.
6. Gradually add automation, testing, observability, and AI-assisted troubleshooting.

Planned next steps include:

* observe naturally occurring alert behavior before deciding whether notification delivery is justified
* add Ingress and TLS when a cleaner private-lab access model becomes the next bounded milestone
* evaluate Loki and OpenTelemetry only when a specific operational question requires them
* maintain the bounded ForgeOps v1 release and require new work to improve the final incident-copilot demonstration, prove trustworthiness, or prepare a future release; model and retrieval integration remain deferred because the demonstration identified no concrete unmet operator question
* follow the [ForgeOps post-v1 improvement roadmap](docs/roadmaps/forgeops-post-v1-roadmap.md) for separately approved demonstration, trust, and future-release candidates
* follow the [Workbench security-guidance roadmap](docs/roadmaps/forge-yaml-workbench-security-guidance-roadmap.md) for a browser-local NIST SP 800-190 profile with selected SP 800-53 references and no compliance claim

## Why this project exists

The Foundry Initiative is not just a code repository.

It is a structured way to rebuild momentum, sharpen technical skills, and create visible proof of engineering growth through practical systems.

The purpose is to build useful artifacts, document the process, and turn learning into a portfolio of working evidence.
