# ForgeOps post-v1 improvement roadmap

**Status:** Proposed sequence; implementation requires separate milestone
approval

**Baseline:** ForgeOps v1.0.0 at tag `forgeops-v1.0.0`

**Roadmap date:** 2026-09-19

## Purpose

This roadmap identifies improvements from the supported v1 baseline through
possible v2 and v3 horizons. The sequence should make the final
incident-copilot demonstration clearer, make its trust claims easier to verify,
or prepare a later ForgeOps release. It does not reopen the accepted v1.0.0
release or authorize implementation by itself.

Every candidate must serve at least one governing purpose:

1. directly improve the final incident-copilot demonstration;
2. prove that the demonstration and released behavior are trustworthy; or
3. prepare a deliberate future release.

Work that cannot name and test one of those purposes is rejected or deferred.

## Preserved baseline

All post-v1 work must preserve these boundaries unless a later milestone
explicitly proposes, justifies, tests, and receives approval for a narrower
change:

- bounded read-only live collection with an explicit kubeconfig, context, and
  optional application URLs;
- deterministic, strict, offline artifact processing;
- visible uncertainty, unmapped deltas, and separate exit domains;
- exact expectations and reproducible evidence where practical;
- informational runbook references rather than diagnosis or execution
  authority;
- no ambient credentials, autonomous remediation, background service, or
  in-cluster ForgeOps identity; and
- no claim that a checksum, structural validation, or mutually consistent
  artifact set proves authenticity or chain of custody.

The `forgeops-v1.0.0` tag and its two release assets remain immutable. Later
documentation or implementation commits must not move the tag or replace those
assets.

## Version horizons

| Horizon | Intended result | Admission boundary |
| --- | --- | --- |
| v1.x | Make the released deterministic demonstration easier to run, challenge, and verify | Backward-compatible improvement with no collection- or remediation-authority expansion |
| v2 | Generalize the deterministic operator path through explicit target profiles, ordered incident timelines, and portable evidence bundles | A demonstrated operator or reviewer need justifies a major compatibility boundary and migration plan |
| v3 | Add evaluated assistive reasoning only if it measurably answers a question the v2 deterministic baseline cannot | Independent corpus, measurable improvement, privacy and failure design, untrusted-draft treatment, and an explicit stop decision |

Version numbers are outcomes of accepted scope, not deadlines. If a horizon
does not satisfy its admission boundary, ForgeOps remains on the last supported
baseline without creating release work.

## Horizon 1 — v1.x demonstration and trust hardening

### Milestone 066 — Installed-artifact demonstration runner

**Purpose:** Improve the final demonstration and prove trustworthiness.

Create a review-first repository script that runs the existing synthetic
evidence-to-brief path through an explicitly selected, verified ForgeOps
installation. It should record the executing provenance, exact input paths,
command-domain exit codes, and produced artifact paths in an operator-selected
temporary directory.

Acceptance must prove that the runner:

- invokes existing public commands rather than reimplementing their logic;
- defaults to the offline synthetic track and has no kubeconfig, kubectl, HTTP,
  network, or mutation path;
- stops on validation-domain errors while preserving comparison and mapping
  difference exits as data;
- produces the same brief and replay result as the manual guide; and
- cleans up only an exact operator-approved temporary directory.

### Milestone 067 — Trust-failure demonstration

**Purpose:** Prove that the incident-copilot demonstration is trustworthy.

Add a compact, offline challenge set that deliberately alters one boundary at
a time: evidence bytes, chronology, summary counts, mapping facts, expected
brief content, and integrity records. Demonstrate that each invalid or
non-matching case fails in its documented domain without being relabeled as a
health conclusion.

Acceptance must include exact expected exits and stable diagnostic fragments.
The challenge set is synthetic negative evaluation data, not evidence of a
live incident or proof that every possible tampering method is detected.

### Milestone 068 — Cross-platform installed-release acceptance

**Purpose:** Prove release trustworthiness and prepare a future release.

Turn the accepted Linux CI and independent Windows installation evidence into
a maintained installed-wheel acceptance matrix. Evaluate whether macOS adds a
meaningful portability claim before adding it; do not add a platform only to
increase matrix size.

Acceptance must install one exact locally supplied wheel without a registry,
run provenance, exercise console and module entry points, validate an unhealthy
but structurally valid artifact, and replay the stable scenario. Source-tree
success cannot substitute for installed-wheel success.

### Milestone 069 — Evidence-bundle manifest decision

**Purpose:** Improve the demonstration and prove trustworthiness.

Design and evaluate a deterministic manifest that inventories one demonstration
session's supplied inputs and produced outputs with schema names, byte lengths,
SHA-256 digests, tool provenance, and command-domain exits. Decide whether the
manifest materially improves review and replay before implementing it.

The design must distinguish internal consistency from authenticity. It must
not imply authorship, signing, time authority, custody, diagnosis, or
remediation permission.

### Milestone 070 — Release provenance and verification decision

**Purpose:** Prove trustworthiness and prepare a future release.

Evaluate whether GitHub artifact attestations, signed checksums, or another
bounded mechanism would improve on the current unsigned SHA-256 record for the
actual operator workflow. The decision must cover identity, offline
verification, key or issuer trust, failure behavior, recovery, maintenance
cost, and what claims remain impossible.

The acceptable outcome may be a documented deferral. No signing service,
dependency, secret, or release permission is introduced until a separately
approved design demonstrates proportionate value.

### Milestone 071 — ForgeOps v1.1 readiness assessment

**Purpose:** Prepare a future release.

After the accepted post-v1 improvements are complete, audit the exact proposed
v1.1 scope, compatibility, schemas, documentation, license, test inventory,
reproducibility, and installation path. Decide whether the changes justify a
minor release, a patch release, or no release.

This milestone is admitted only when at least one operator-visible improvement
has been accepted. A version number must not create work by itself.

### Milestone 072 — ForgeOps v1.1 candidate, release, and closeout

**Purpose:** Prepare and complete a future release.

This conditional milestone may begin only after Milestone 071 identifies an
accepted release scope. It must reproduce the candidate, test the exact wheel
across the declared support range, publish only reviewed assets from an exact
tag, independently install the public artifact, preserve rollback, and record
the final boundary.

If readiness fails, release work stops without creating a tag or modifying the
v1.0.0 release.

## Horizon 2 — deterministic ForgeOps v2

ForgeOps v2 would remain deterministic, read-only, and informational. Its
major-version justification would be a deliberate generalization beyond the
SignalForge-specific pairwise evidence path, not model integration or
remediation.

### Milestone 073 — v2 problem statement and compatibility boundary

**Purpose:** Improve the demonstration and prepare a future release.

Use accepted v1.x demonstrations to identify the exact operator and reviewer
needs that require a v2 boundary. Define supported v1 artifacts, migration,
compatibility, versioning, and explicit exclusions before changing a schema or
command.

Acceptance may conclude that v2 is not justified. In that case, later v2
milestones remain deferred.

### Milestone 074 — Declarative target-profile design

**Purpose:** Improve the demonstration and prove trustworthiness.

Design a strict, versioned profile that replaces compiled SignalForge target
constants with an explicitly supplied allowlist of named resources and
optional endpoints. Profiles must not enable ambient discovery, Secrets,
broad namespace reads, arbitrary commands, credential embedding, or mutation.

The design must define profile validation, size and count limits, canonical
ordering, redaction, provenance limitations, and how a profile is bound to its
evidence.

### Milestone 075 — Deterministic target-profile implementation

**Purpose:** Improve the demonstration and prepare v2.

Implement only the accepted profile contract through the existing deny-by-
default runners. Preserve an explicit kubeconfig and exact context for every
live read, and prove that invalid or overbroad profiles fail before collection.

The fixed SignalForge profile remains a supported migration and regression
fixture until an approved compatibility decision says otherwise.

### Milestone 076 — Ordered incident timeline

**Purpose:** Improve the demonstration.

Extend deterministic comparison from one before/after pair to a bounded,
strictly ordered sequence of validated snapshots. Render observed transitions,
recoveries, persistent unknowns, and mapping coverage without inferring cause,
severity, impact, or remediation.

Acceptance requires exact timeline expectations, chronology and duplicate
rejection, bounded input counts and sizes, stable ordering, and equivalence
between structured and operator-facing views.

### Milestone 077 — Portable evidence bundle

**Purpose:** Improve the demonstration, prove trustworthiness, and prepare v2.

If Milestone 069 accepts the manifest concept, implement a bounded portable
bundle containing only explicitly selected validated artifacts, their
manifest, and deterministic replay inputs. Bundle creation and verification
must work offline and must not silently collect, rewrite, or authenticate the
underlying evidence.

### Milestone 078 — Profile-aware runbook knowledge

**Purpose:** Improve the demonstration.

Allow deterministic mapping to select an explicitly supplied, validated
catalog appropriate to the active target profile. Catalog selection must be
visible in the evidence chain and cannot prove that a runbook applies or
authorize its execution.

This milestone is admitted only if v2 profile demonstrations expose a concrete
catalog-selection need.

### Milestone 079 — v2 adversarial and compatibility evaluation

**Purpose:** Prove that v2 is trustworthy.

Challenge profile confusion, cross-profile artifact mixing, reordered or
truncated timelines, malicious bundle paths, stale catalogs, v1 migration, and
forbidden claims. Compare all accepted behavior with the v1 deterministic
baseline and document every intentional incompatibility.

### Milestone 080 — ForgeOps v2 readiness, candidate, release, and closeout

**Purpose:** Prepare and complete the v2 release.

Audit the accepted v2 scope, schemas, migration path, documentation, test
inventory, reproducibility, platform support, artifact set, and rollback.
Build and independently accept the exact candidate before any tag or public
asset is created.

If the v2 contract, migration, or trust evaluation is incomplete, release work
stops and the supported v1.x baseline remains unchanged.

## Horizon 3 — conditional assistive ForgeOps v3

ForgeOps v3 is not promised. It is a conditional horizon for evaluated model
or retrieval assistance only if deterministic v2 demonstrations identify a
concrete unanswered operator question. The deterministic pipeline remains the
authority-bearing source of facts; probabilistic output remains untrusted
draft text with no live-system or remediation authority.

### Milestone 081 — v3 admission and stop decision

**Purpose:** Improve the demonstration and prevent unjustified scope.

Review v2 demonstrations and operator feedback for one concrete unanswered
question. Record a measurable success threshold and determine whether model or
retrieval assistance is plausibly necessary.

If no qualifying gap exists, stop the v3 sequence. Continuing because an AI
feature is fashionable is an explicit failure of this gate.

### Milestone 082 — Independent assistive-reasoning evaluation corpus

**Purpose:** Prove trustworthiness.

Create an evaluation corpus independent of model training and prompt tuning.
It must include answerable, unanswerable, conflicting, incomplete, adversarial,
and forbidden-claim cases with scoring for factual support, citations,
abstention, uncertainty, and authority-boundary compliance.

### Milestone 083 — v3 privacy, threat, dependency, and failure design

**Purpose:** Prove trustworthiness and prepare v3.

Decide local versus remote processing, data minimization, retention, model and
retrieval dependencies, timeouts, unavailability behavior, prompt-injection
treatment, update policy, and operator disclosure. No kubeconfig, credential,
endpoint, collection, persistence, or mutation authority may reach the
assistive component.

### Milestone 084 — Offline assistive-reasoning experiment

**Purpose:** Improve the demonstration.

Run a bounded experiment using only validated, redacted v2 evidence bundles.
Compare its answers with the deterministic brief and the independent corpus.
Output must be visibly labeled untrusted draft assistance and must fail closed
to the deterministic baseline when unavailable or invalid.

This experiment is not yet a supported ForgeOps feature or release candidate.

### Milestone 085 — Citation and forbidden-claim enforcement

**Purpose:** Prove trustworthiness.

Require every assistive factual claim to resolve to supplied evidence or
catalog material, and reject unsupported causation, severity, impact,
applicability, current-health, and remediation-authority claims. Evaluate
enforcement independently from model quality.

### Milestone 086 — Comparative operator evaluation

**Purpose:** Improve the demonstration and prove trustworthiness.

Compare deterministic-only and assistive workflows on the admitted operator
question. Measure correctness, unsupported claims, abstention, time to answer,
review burden, reproducibility, and failure recovery.

The assistive path advances only if it clears the predeclared threshold without
weakening the deterministic baseline or authority boundaries.

### Milestone 087 — ForgeOps v3 readiness assessment

**Purpose:** Prepare a future release.

Audit whether the evaluated assistive path is supportable across privacy,
quality, dependency, platform, cost, failure, upgrade, rollback, and operator-
disclosure boundaries. The acceptable outcome is deferral or rejection.

### Milestone 088 — ForgeOps v3 candidate, release, and closeout

**Purpose:** Prepare and complete a conditional v3 release.

Begin only after Milestone 087 accepts an exact scope. Prove the deterministic
core independently, evaluate the exact assistive dependency and configuration,
publish only reviewed artifacts, independently accept the public release, and
document how to disable or remove assistance while retaining deterministic
operation.

If any v3 trust threshold fails, no tag or public release is created.

## Conditional add-ons

The following are not scheduled milestones. Each needs new evidence before it
can enter the sequence:

| Candidate | Admission evidence | Governing purpose |
| --- | --- | --- |
| Static HTML demonstration report | A reviewer cannot efficiently understand or share the deterministic text and JSON brief | Improve the demonstration |
| Additional synthetic incident families | A concrete failure mode is absent from the current corpus and has a deterministic expected result | Improve the demonstration; prove trustworthiness |
| Broader runbook catalog | A demonstrated delta remains unmapped and an authoritative repository runbook exists | Improve the demonstration |
| Model or retrieval experiment | Milestone 081 admits one concrete question that v2 cannot answer, with an independent evaluation corpus and measurable threshold | Improve the demonstration |
| Additional live telemetry | A specific operational question cannot be answered by existing bounded evidence | Improve the demonstration |

Forge YAML Workbench configuration guidance is planned separately in the
[Workbench security-guidance roadmap](forge-yaml-workbench-security-guidance-roadmap.md).
Its first NIST profile remains browser-local and does not become ForgeOps
evidence without a later demonstrated need and separately approved artifact
contract.

## Rejected or deferred work

- Autonomous or one-click remediation remains rejected because ForgeOps has no
  remediation authority.
- A conversational model, vector database, embedding service, or external API
  remains deferred because the accepted demonstration identified no unmet
  operator question.
- Forced live failure injection remains deferred; synthetic incidents already
  demonstrate degraded behavior without changing the cluster.
- Loki, OpenTelemetry, broader Kubernetes discovery, and additional dashboards
  remain deferred until a named operational question requires them.
- PyPI publication, a containerized ForgeOps service, an in-cluster deployment,
  and a background agent remain deferred because they do not currently improve
  the accepted operator path enough to justify their authority and maintenance
  cost.
- UI polish, additional output formats, and integrations are rejected when
  their only rationale is novelty or technology exposure.

## Milestone admission checklist

Before any candidate becomes an active milestone, its proposal must state:

1. which governing purpose it serves;
2. the concrete operator or reviewer outcome it improves;
3. the accepted baseline and exact scope;
4. the offline, live, network, credential, persistence, and mutation boundaries;
5. deterministic acceptance criteria and negative cases;
6. whether package, release, deployment, or live-system gates apply;
7. rollback or safe abandonment behavior; and
8. why the work is preferable to leaving the v1 baseline unchanged.

Approval of this roadmap is approval of direction only. Planning,
implementation, publication, live access, release, merge, and cleanup remain
explicit gates for each admitted milestone.

## Success measure

Post-v1 work succeeds when a reviewer can run or inspect the demonstration more
easily, verify a stronger bounded trust claim, or install a deliberately
prepared later release. More components, commands, integrations, or milestone
numbers are not success by themselves.
