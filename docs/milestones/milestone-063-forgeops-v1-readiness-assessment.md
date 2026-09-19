# Milestone 063 — ForgeOps v1 readiness assessment

**Status:** Complete and merged through PR #66; documentation-only closeout in
progress

**Started:** 2026-09-19

## Governing purpose

This milestone prepares the v1 release. It converts the accepted deterministic
incident-copilot demonstration into bounded, testable release criteria without
adding product capability.

## Outcome

The assessment confirms that ForgeOps needs one release-candidate hardening
milestone before release. Milestone 064 is therefore required; it is not filler
work. Milestone 065 remains the release and closeout milestone.

The accepted release channel is a GitHub Release containing a ForgeOps wheel
and SHA-256 checksums. PyPI publication is excluded. The accepted public reuse
license is MIT. Product-specific tag `forgeops-v1.0.0` will avoid collision with
the repository's existing product tags.

See the [v1 release-readiness decision](../design/forgeops-v1-release-readiness.md)
for satisfied evidence, seven release blockers, exclusions, and the remaining
milestone sequence.

## Read-only audit evidence

- Reviewed the roadmap, project status, testing guide, operator guide, snapshot
  runbook, contribution workflow, package metadata, ForgeOps workflow, command
  parser, provenance implementation, and relevant tests.
- Confirmed package version `0.15.0`, Python declaration `>=3.11`, no runtime
  dependencies, and one root distribution currently named `foundry-check`.
- Confirmed ForgeOps CI installs from the checkout on Python 3.12 and exercises
  every current top-level command family, but does not build and reinstall the
  exact candidate wheel or prove the full declared Python range.
- Built `foundry_check-0.15.0-py3-none-any.whl` locally from the reviewed source.
- Installed the wheel into a fresh Python 3.12 environment using `--no-index`.
- Installed provenance returned `OK` with matching distribution and module
  versions and identified the exact wheel as the installation source.
- Console and `python -m forgeops` help rendered, strict evidence validation
  passed, and stable scenario replay matched.
- Confirmed the repository and wheel lack license metadata and that the
  repository has no ForgeOps release tag or ForgeOps artifact-publication
  workflow.

The audit used no kubeconfig, kubectl, application endpoint, live system,
registry publication, GitHub tag, release, external service, deployment, or
mutation.

## Explicit exclusions

This milestone changes documentation only. It does not change package identity,
version, code, tests, schemas, dependencies, CI behavior, permissions, tags,
artifacts, registries, deployments, live systems, or authority. Those changes
belong only to the separately reviewable Milestone 064 candidate.

## Approval gates

1. Planning approval — complete; Mike approved Milestones 063–065 and their
   gates.
2. Read-only assessment and decision — complete.
3. Documentation implementation and validation — complete; all 204 repository
   Python tests passed, as did Python compilation, Kubernetes manifest, Wiki,
   alert-rule source, and whitespace validation.
4. Package or image release — closed as not applicable; this assessment
   publishes no artifact.
5. Deployment — closed as not applicable.
6. Live acceptance — closed as not applicable; the assessment uses existing
   accepted evidence and an offline wheel-install check.
7. Acceptance review and PR readiness — complete; accepted remote head
   `25b9340b56b58af7fd8f88fdffcf82d1ed7ed5e9` resolved to tree
   `d407063392c9294fc8aed27a747744ee1c111201`, exactly matching the validated
   local tree, and PR #66 was marked ready. GitHub Actions did not run because
   the documentation-only paths were outside the workflow filters.
8. Merge — complete; PR #66 was squash-merged at
   `2293865859ddc6259f8cedee95705e800a152bc6`.
9. Documentation-only closeout — in progress; this update records the accepted
   assessment and merge without adding release or operational authority.
10. Branch cleanup and synchronization — pending.

## Merge and publication evidence

- Accepted implementation head: `25b9340b56b58af7fd8f88fdffcf82d1ed7ed5e9`.
- Exact accepted tree: `d407063392c9294fc8aed27a747744ee1c111201`.
- Implementation PR: #66.
- Squash merge: `2293865859ddc6259f8cedee95705e800a152bc6`.
- Package publication, release tag, deployment, and live acceptance remained
  not applicable.

## Acceptance boundary

Milestone 063 is accepted only when the repository records the release contract,
the evidence already satisfied, every identified blocker, explicit exclusions,
and the bounded Milestone 064–065 sequence. It cannot declare a v1 candidate or
release ready.
