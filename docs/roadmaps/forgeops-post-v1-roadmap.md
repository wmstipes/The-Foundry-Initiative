# ForgeOps post-v1 improvement roadmap

**Status:** Proposed sequence; implementation requires separate milestone
approval

**Baseline:** ForgeOps v1.0.0 at tag `forgeops-v1.0.0`

**Roadmap date:** 2026-09-19

## Purpose

This roadmap identifies the next improvements that could make the final
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

## Recommended sequence

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

## Conditional add-ons

The following are not scheduled milestones. Each needs new evidence before it
can enter the sequence:

| Candidate | Admission evidence | Governing purpose |
| --- | --- | --- |
| Static HTML demonstration report | A reviewer cannot efficiently understand or share the deterministic text and JSON brief | Improve the demonstration |
| Additional synthetic incident families | A concrete failure mode is absent from the current corpus and has a deterministic expected result | Improve the demonstration; prove trustworthiness |
| Broader runbook catalog | A demonstrated delta remains unmapped and an authoritative repository runbook exists | Improve the demonstration |
| Model or retrieval experiment | A concrete operator question remains unanswered by the deterministic brief, with an independent evaluation corpus and measurable threshold | Improve the demonstration |
| Additional live telemetry | A specific operational question cannot be answered by existing bounded evidence | Improve the demonstration |

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
