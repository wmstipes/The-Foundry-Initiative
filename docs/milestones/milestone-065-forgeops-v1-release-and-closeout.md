# Milestone 065 — ForgeOps v1 release and closeout

**Status:** ForgeOps v1.0.0 published and independently accepted; release-record
merge, documentation-only closeout, and branch cleanup remain

**Started:** 2026-09-19

## Governing purpose

This milestone prepares and completes the v1 release. It publishes only the
exact candidate accepted in Milestone 064, proves the published assets through
an independent operator installation, and records the durable v1 boundary.

## Release identity

- Product: ForgeOps
- Distribution: `signalforge-forgeops`
- Version: `1.0.0`
- Tag: `forgeops-v1.0.0`
- Tagged source: `9f86d2ceefd40e58282190711ec5e2eb69adba6f`
- Release: <https://github.com/wmstipes/The-Foundry-Initiative/releases/tag/forgeops-v1.0.0>
- Release workflow run: `35465207955`
- Wheel: `signalforge_forgeops-1.0.0-py3-none-any.whl`
- Wheel size: 51,589 bytes
- Wheel SHA-256:
  `be4d0a3001dac9bbbeec819327379461e27a7255557f6bdd66fd69d81ee7fc19`
- Checksum asset: `SHA256SUMS.txt`
- Checksum-asset SHA-256:
  `17212936c37ad55356267c25f41f8eb03262f3957e79f46a8c4747c5921593f5`
- License: MIT
- Supported Python: 3.11-3.14

## Pre-publication reconfirmation

- Milestone 064 Gate 10 ended with clean synchronized `main` at the exact
  closeout commit, only local and remote `main`, no Milestone 064 branches, and
  no retained candidate directory.
- Two fresh local builds from the synchronized closeout tree passed strict
  validation, were byte-identical, and reproduced the accepted wheel digest.
- The annotated tag was created only after verifying that it did not already
  exist and that it resolved to the accepted source commit.
- No source, package input, workflow, release note, dependency, or authority
  changed between candidate acceptance and the release tag.

## Publication evidence

- GitHub Actions accepted the exact product tag and completed all ten jobs:
  four tagged-source tests, one exact reproducible build, four exact-wheel
  offline install-and-smoke jobs, and one final publication job.
- Python 3.11, 3.12, 3.13, and 3.14 passed both the tagged-source and
  exact-wheel matrices.
- Both tagged builds produced the accepted 51,589-byte wheel and exact SHA-256;
  strict validation passed twice before publication.
- The final job published a non-draft, non-prerelease GitHub Release containing
  exactly two assets: the reviewed wheel and `SHA256SUMS.txt`.
- The workflow published nothing to PyPI, built no container, accessed no
  cluster or application endpoint, and performed no deployment or remediation.

## Independent published-asset acceptance

- The Windows operator resolved the local tag to the accepted source and
  confirmed the public release identity and final state through GitHub.
- The operator downloaded only the two release assets into a fresh temporary
  directory and rejected missing or additional files.
- The downloaded checksum asset matched its GitHub-recorded digest. Its wheel
  record and an independent SHA-256 calculation both matched the accepted
  wheel digest.
- A fresh Python 3.14.7 environment installed the public wheel with
  `--no-index`.
- Provenance returned `OK`, distribution `signalforge-forgeops`, matching
  distribution and module version `1.0.0`, execution mode `local-install`, and
  paths inside the isolated environment.
- Console and module help succeeded. Strict evidence validation preserved the
  contained `UNKNOWN`/exit-2 state without turning it into validation failure,
  and stable scenario replay returned exact `MATCH` with zero deltas.

## Preserved v1 boundaries

ForgeOps v1 remains a deterministic, bounded incident copilot. It can collect
only its explicit read-only snapshot, validate and compare supplied evidence,
create and verify local integrity records, replay synthetic expectations, map
catalog rules, and render deterministic incident briefs.

It does not establish causation, operational severity, impact, runbook
applicability, current health beyond supplied point-in-time evidence, or
remediation authority. It includes no model, retrieval service, autonomous
agent, PyPI package, container, deployment, background service, broader
telemetry collection, package signature, attestation, or chain-of-custody
system. The `v1alpha1` evidence schemas remain intentionally distinct from the
package's v1 release number.

## Approval gates

1. Planning approval — complete; Mike approved Milestones 063-065 and all
   respective gates.
2. Exact source and candidate reconfirmation — complete.
3. Tag identity and pre-publication review — complete.
4. GitHub Release publication — complete through workflow run `35465207955`.
5. Deployment — closed as not applicable; ForgeOps v1 is a local wheel.
6. Independent published-asset acceptance — complete on Windows Python 3.14.7.
7. Release acceptance review — complete; published identity, asset set,
   checksums, provenance, and offline behavior all match the accepted candidate.
8. Release-record merge — pending.
9. Documentation-only closeout — pending.
10. Branch and temporary-artifact cleanup — pending.

## Acceptance boundary

The release is accepted only as the exact tagged wheel and checksum described
above. GitHub-generated source archives are review conveniences, not the
supported operator artifact. A matching unsigned checksum detects byte changes
relative to the separately reviewed value but does not prove authorship or
chain of custody.
