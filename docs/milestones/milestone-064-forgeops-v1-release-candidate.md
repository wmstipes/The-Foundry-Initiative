# Milestone 064 — ForgeOps v1 release-candidate hardening

**Status:** Candidate accepted through draft PR #68, independent CI, and fresh
Windows operator validation. Merge and closeout remain pending. No tag or
release has been created.

**Started:** 2026-09-19

## Governing purpose

This milestone proves trustworthiness and prepares the v1 release. It resolves
only the seven blockers accepted in Milestone 063 and does not add incident
reasoning, collection, deployment, or remediation capability.

## Candidate scope

1. Give the wheel the explicit distribution identity
   `signalforge-forgeops`, expose only the `forgeops` entry point, and exclude
   the legacy `foundry-check` package from the v1 artifact.
2. Align package, module, provenance, documentation, tests, and the future tag
   on version `1.0.0`.
3. Build the exact wheel twice with a fixed build backend and timestamp, require
   byte-identical output, generate `SHA256SUMS.txt`, and strictly validate the
   two-file candidate.
4. Declare and prove Python 3.11-3.14 through source and exact-wheel CI matrices.
5. Add the accepted MIT license to repository and wheel metadata.
6. Add a product-tag-only GitHub Release workflow with read-only defaults and
   write authority confined to the final publication job.
7. Document checksum verification, isolated offline installation, provenance,
   command smoke checks, clean replacement, rollback, and removal.

## Preserved boundaries

- The candidate is not a public release and Milestone 064 creates no tag.
- No PyPI publication, container build, deployment, cluster access, application
  endpoint access, external service, or live-system mutation is authorized.
- ForgeOps remains offline-first after explicitly bounded collection.
- Evidence and incident outputs remain deterministic and retain their separate
  exit domains.
- Runbook matches and incident briefs remain informational only. They do not
  establish causation, severity, impact, applicability, or remediation
  authority.
- Model, retrieval, broader telemetry, orchestration, and schema renaming remain
  deferred.

## Approval gates

1. Planning approval — complete; Mike approved Milestones 063-065 and every
   respective gate.
2. Local implementation and validation — complete.
3. Draft PR, exact candidate artifact, and CI proof — complete; PR #68 at
   remote head `352a5eb` produced retained artifact `forgeops-v1-candidate`
   from workflow run `35463673504`. All nine build, source-test, and exact-wheel
   install jobs passed across Python 3.11-3.14.
4. Package publication — closed as not applicable; a retained CI candidate is
   review evidence, not a release.
5. Deployment — closed as not applicable.
6. Fresh Windows operator candidate installation and offline acceptance —
   complete on Python 3.14.7.
7. Acceptance review and PR readiness — pending this documentation
   reconciliation and its required CI rerun.
8. Merge — pending.
9. Documentation-only closeout — pending.
10. Branch cleanup and synchronization — pending.

## Stop condition

Milestone 065 must not create the `forgeops-v1.0.0` tag or publish a GitHub
Release unless this exact candidate passes local validation, CI across every
declared Python minor version, and the fresh operator acceptance path. Approval
does not convert failed or missing evidence into acceptance.

## Local validation evidence

- The first strict artifact validation caught stale `build/` content that would
  have bundled `foundry_check` in the wheel. The candidate was rejected before
  acceptance. The build helper now stages only `pyproject.toml`, `README.md`,
  `LICENSE`, and `src/forgeops` into a fresh temporary source tree.
- Two subsequent builds produced byte-identical 51,589-byte wheels and identical
  checksum files. Strict validation accepted only the exact ForgeOps package and
  metadata manifest. The local candidate digest was
  `be4d0a3001dac9bbbeec819327379461e27a7255557f6bdd66fd69d81ee7fc19`.
- A fresh Python 3.12 environment installed that exact wheel with `--no-index`.
  Provenance returned `OK` for distribution and module version `1.0.0` and the
  full offline command-family smoke path completed against reviewed fixtures.
- All 151 focused ForgeOps tests, 209 top-level Python tests, and 214 complete
  repository Python tests passed. Python compilation, Kubernetes manifest,
  Wiki front-door, alert-rule source, workflow YAML, and whitespace validation
  also passed.
- The unchanged Workbench suite was not rerun locally because its dependencies
  were unavailable in this workspace; its dedicated workflow remains separate
  from the ForgeOps candidate path.

The local checksum is validation evidence, not a release identifier. Gate 3 CI
must independently build, validate, retain, and install the candidate before
operator acceptance.

## CI and operator acceptance evidence

- The remote candidate commit `352a5eb9d66dd3357c4c387fa21af765756ef1c4`
  resolved to tree `523c99cd1f8c12a7558dc2dc1b81977f0da2d036`, exactly matching the
  locally validated tree.
- ForgeOps CI run `35463673504` passed one reproducible-build job, four source
  test jobs, and four exact-wheel install-and-smoke jobs. Python 3.11, 3.12,
  3.13, and 3.14 all passed both relevant matrices.
- Both CI builds reproduced the local 51,589-byte wheel with SHA-256
  `be4d0a3001dac9bbbeec819327379461e27a7255557f6bdd66fd69d81ee7fc19`.
  Strict artifact validation passed twice before CI retained exactly the wheel
  and checksum as `forgeops-v1-candidate` for 14 days.
- On Windows, the operator downloaded that named artifact directly from the CI
  run and required exactly the two expected files. The checksum record, known CI
  digest, and independently calculated wheel digest all matched.
- A fresh Python 3.14.7 virtual environment installed the wheel with
  `--no-index`. Provenance reported `OK`, distribution
  `signalforge-forgeops`, matching distribution and module version `1.0.0`,
  execution mode `local-install`, and paths inside the isolated environment.
- Console and module help succeeded. Strict validation accepted the reviewed
  `UNKNOWN` golden artifact while preserving its contained exit domain, and the
  stable scenario replay returned an exact `MATCH` with zero deltas.

This evidence accepts the candidate for merge. It does not publish the package,
establish current cluster health, or grant remediation authority. The retained
operator directory remains temporary evidence until Milestone 064 closeout.
