# Forge YAML Workbench security-guidance roadmap

**Status:** Proposed Workbench-first sequence; implementation requires a
separate milestone approval

**Baseline:** Forge YAML Workbench 0.10.0 with the pinned OWASP Kubernetes Top
10:2025 review profile

**Roadmap date:** 2026-09-19

## Purpose

This roadmap extends Forge YAML Workbench configuration guidance with a bounded
NIST layer while preserving browser-local analysis and the distinction between
manifest-visible signals and evidence that requires a cluster, pipeline,
runtime, process, or organization.

The track serves two governing purposes:

1. prove that security guidance is traceable, deterministic, and honest about
   its evidence limits; and
2. prepare a deliberate future Workbench release.

It does not authorize implementation, declare compliance, or expand ForgeOps.

## Source hierarchy

### Primary configuration source — NIST SP 800-190

[NIST SP 800-190, Application Container Security Guide](https://csrc.nist.gov/pubs/sp/800/190/final)
is the primary source because it addresses container security concerns and
recommendations. A Workbench profile would translate only guidance with a
defensible manifest-visible signal.

### Control references — NIST SP 800-53 Release 5.2.0

Selected controls from
[NIST SP 800-53 Rev. 5](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final)
may be attached as traceable references. The profile must pin the exact NIST
release and identify the reviewed control text or OSCAL source.

An 800-53 reference is not a control assessment. NIST describes the catalog as
flexible and customizable within an organization-wide risk process and warns
that mappings and crosswalks are not necessarily one-to-one or equivalent.

### Lifecycle context — NIST SP 800-37 Revision 2

[NIST SP 800-37 Revision 2](https://csrc.nist.gov/pubs/sp/800/37/r2/final)
defines the Risk Management Framework lifecycle. Workbench may label where a
manifest observation could support an RMF activity, but it does not execute the
RMF or replace the accountable organizational roles, decisions, and evidence
required by that process.

### Assessment-method reference — NIST SP 800-53A Release 5.2.0

[NIST SP 800-53A Revision 5](https://csrc.nist.gov/pubs/sp/800/53/a/r5/final)
may inform assessment-support metadata. Workbench can only examine the supplied
YAML. It cannot interview personnel, test a running control, determine that a
control operates as intended, or issue a control assessment result.

### User-supplied baselines — NIST SP 800-53B

[NIST SP 800-53B](https://csrc.nist.gov/pubs/sp/800/53/b/upd1/final) may be
referenced only when an operator explicitly supplies an applicable baseline or
tailored profile. Workbench must not infer a Low, Moderate, or High impact
baseline, select organizational controls, or treat a generic baseline as an
authorization boundary.

### Outcome orientation — NIST Cybersecurity Framework 2.0

[NIST CSF 2.0](https://www.nist.gov/cyberframework) may organize high-level
portfolio and report outcomes. It must not be converted into individual YAML
pass/fail checks when a manifest cannot establish the outcome.

### Deferred source — NIST SP 800-204C

[NIST SP 800-204C](https://csrc.nist.gov/pubs/sp/800/204/c/final) may later
inform pipeline or microservices guidance. It is not part of the first profile
because the current Workbench analyzes supplied YAML rather than a DevSecOps
pipeline or service mesh.

### Deferred interchange — OSCAL

An OSCAL component-definition, assessment-results, or other machine-readable
export remains deferred until a named downstream workflow and exact schema
boundary justify it. Adding OSCAL only to advertise format support would create
false interoperability and maintenance claims.

## RMF applicability boundary

| RMF step | Bounded Workbench role | Explicit exclusion |
| --- | --- | --- |
| Prepare | Identify pinned sources, evidence scope, and missing context | No organizational risk strategy, role assignment, or system-level preparation |
| Categorize | Report that impact categorization is required context | No inference of information types, impact values, or system category from YAML |
| Select | Display references from an explicitly supplied profile or baseline | No automatic baseline selection, tailoring, overlays, or organizational control decision |
| Implement | Record manifest-visible configuration evidence related to a selected control | No conclusion that the complete control is implemented or effective |
| Assess | Produce assessment-supporting observations using only the `examine` method | No interviews, runtime tests, satisfied/not-satisfied determination, or assessment report |
| Authorize | State that authorization evidence and accountable review remain external | No authorization recommendation, risk acceptance, ATO, or authorization decision |
| Monitor | Export point-in-time observations for possible external reuse | No continuous-monitoring, current-health, drift-detection, or ongoing-authorization claim |

The initial RMF-aligned report is an evidence appendix, not an RMF dashboard,
score, checklist completion meter, system security plan, assessment report,
plan of action and milestones, authorization package, or authorization to
operate.

## Preserved boundaries

Every candidate must preserve:

- browser-local parsing and analysis;
- no upload, server-side persistence, Kubernetes API access, live discovery,
  credentials, network request, model, retrieval service, or mutation;
- explicit Kubernetes mode and the existing supported-GVK boundary;
- deterministic findings derived only from supplied YAML and pinned profile
  data;
- separate `direct`, `partial`, and `cluster-context-required` applicability;
- no claim of NIST, federal, FISMA, FedRAMP, CSF, or 800-53 compliance;
- no inferred impact categorization, control baseline, tailoring decision,
  assessment determination, risk acceptance, authorization, or ongoing
  monitoring status;
- no `satisfied`, `not satisfied`, `implemented`, `effective`, `authorized`, or
  equivalent status derived from supplied YAML;
- no claim about effective RBAC, admission, runtime state, image contents,
  supply-chain provenance, logging, monitoring, incident response, policy,
  process, or organizational implementation when the manifest cannot prove it;
  and
- no transfer of Workbench findings into ForgeOps without a separately
  designed and validated artifact boundary.

## Candidate sequence

The labels below are roadmap work packages, not active global milestone
numbers. A candidate receives a normal milestone number only after it passes
the project admission gate.

### Work package W1 — NIST applicability and source decision

**Purpose:** Prove trustworthiness.

Inventory SP 800-190 recommendations and select only those with a clear
relationship to supported Kubernetes manifest fields. Record exclusions and
context-required topics as carefully as included checks.

Acceptance requires exact source versions, section references, rationale,
copyright-safe paraphrases, applicability labels, and an explicit rejection of
compliance scoring.

### Work package W2 — Versioned NIST profile contract

**Purpose:** Prove trustworthiness and prepare a future Workbench release.

Define a pinned browser-local profile containing stable rule identifiers,
source references, manifest scope, severity rationale, evidence fields,
applicability, remediation-neutral guidance, optional selected 800-53 and CSF
references, and optional RMF-support metadata. RMF metadata must use bounded
values for the related step, evidence role, and `examine` method rather than
free-form claims.

The contract must reject duplicate rules, unknown fields, unsupported source
versions, invalid references, hidden network dependencies, and ambiguous
cross-framework equivalence.

### Work package W3 — Browser-local NIST guidance implementation

**Purpose:** Prepare a future Workbench release.

Implement the accepted rules through the existing analyzer seams without
changing file handling, browser-only processing, CSP, cluster access, or
report-authority boundaries.

Candidate manifest-visible themes may include workload privilege, host
namespace sharing, writable filesystems, capability control, runtime identity,
resource constraints, image-reference discipline, and secret-material
placement. Inclusion depends on the W1 source analysis rather than this
illustrative list.

### Work package W4 — OWASP and NIST cross-framework presentation

**Purpose:** Improve review usability and prove trustworthiness.

Show one underlying manifest fact once while preserving every applicable OWASP
and NIST reference. Make source, version, applicability, and evidence visible
without implying that categories or controls are equivalent.

Filtering and counts must not change the analysis, overall result, source
coverage, or Markdown report contents unexpectedly.

### Work package W5 — RMF evidence model and report appendix

**Purpose:** Prove trustworthiness and prepare a future Workbench release.

Define and render a deterministic appendix that connects each applicable
manifest fact to its pinned source, related RMF step, selected control
reference, evidence role, `examine` method, observed fields, and missing
external evidence.

The evidence role must distinguish `implementation-evidence`,
`assessment-input`, and `context-required`. The appendix must not calculate an
RMF progress percentage, aggregate compliance score, control-effectiveness
status, residual risk, authorization recommendation, or ATO readiness result.

### Work package W6 — Adversarial and golden evaluation

**Purpose:** Prove trustworthiness.

Add exact fixtures for positive signals, negative signals, absent fields,
unsupported GVKs, multi-document YAML, misleading names, duplicate keys,
cross-framework overlap, and context-required cases.

Acceptance must prove deterministic ordering, stable identifiers, exact report
output, no network use, no hidden compliance score, and no claim beyond the
supplied manifest. Negative cases must reject inferred categorization,
automatic Low/Moderate/High baseline selection, complete-control assertions,
assessment conclusions, authorization language, continuous-monitoring claims,
and unsupported OSCAL interoperability.

### Work package W7 — Workbench release readiness and release

**Purpose:** Prepare a future release.

Audit profile provenance, source pinning, UI and report clarity, test coverage,
strict-CSP operation, locked dependencies, multi-architecture image build,
rollback, documentation, and live browser behavior before selecting a version.

The readiness decision determines whether the accepted change warrants 0.11.0,
1.0.0, another version, or no release. A version number must not create scope.

## ForgeOps relationship

The first NIST profile belongs only to Forge YAML Workbench. It does not add a
ForgeOps collector, evidence field, finding type, runbook mapping, incident
fact, severity, diagnosis, or recommendation.

A later ForgeOps proposal may be admitted only if an end-to-end demonstration
identifies a concrete operator need for reviewed configuration findings. That
proposal must define a strict versioned artifact, provenance and integrity
limits, stale-data behavior, cross-document consistency, and continued absence
of Workbench or model access to a kubeconfig or live cluster.

## Success measure

The track succeeds when a reviewer receives clearer, source-traceable
configuration guidance from supplied YAML while understanding exactly what the
manifest does and does not prove. An RMF-aligned appendix succeeds only when it
makes evidence reusable without being mistaken for RMF completion, a control
assessment, risk acceptance, or authorization. More framework labels,
findings, controls, or lifecycle steps are not success by themselves.
