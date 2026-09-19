# ForgeOps v1 release-readiness decision

**Decision date:** 2026-09-19

## Purpose

This decision prepares the deterministic ForgeOps incident copilot for a
trustworthy v1 release. It does not add incident reasoning, collection,
recommendation, remediation, model, retrieval, deployment, or cluster
authority.

## Accepted release contract

ForgeOps v1 will be distributed from a GitHub Release as an installable Python
wheel accompanied by SHA-256 checksums. It will not be published to PyPI. The
release will use the product-specific tag `forgeops-v1.0.0` so it cannot be
confused with the repository's Restaurant API or Forge YAML Workbench tags.

The public release will use the MIT License. The exact license text and package
metadata must be reviewed in the release-candidate pull request before they
become part of the release.

GitHub source archives remain useful review material, but the reviewed wheel is
the supported operator artifact. An operator must be able to download the wheel
and checksum file, verify the wheel bytes, install the wheel into an isolated
environment without contacting a package registry, run provenance, and use the
documented command surface.

## Readiness evidence already satisfied

- Milestone 062 proved the existing evidence-to-brief path through a synthetic
  `DEGRADED` scenario and a separate live read-only `STABLE` baseline.
- The demonstration left no concrete operator question unanswered, so model
  and retrieval integration remain deferred.
- The complete repository suite contains 204 Python tests, including 141
  focused ForgeOps tests, with separate Workbench, alert-rule, manifest, Wiki,
  and whitespace validation.
- ForgeOps has no third-party runtime dependency.
- The current `0.15.0` source builds as a pure-Python wheel. A fresh isolated
  Python 3.12 environment installed that wheel with `--no-index`; installed
  provenance returned `OK`, both console and module help rendered, strict
  evidence validation passed, and stable scenario replay matched.
- The wheel contained the reviewed ForgeOps modules and package metadata; no
  Kubernetes configuration, live evidence, credential, or generated
  demonstration artifact was included.

These facts establish a strong release baseline. They do not establish that the
current package identity, release automation, compatibility claim, licensing,
or published artifact is ready for v1.

## Release blockers assigned to Milestone 064

1. **Product and distribution identity.** The current wheel is named
   `foundry_check-0.15.0` and bundles the legacy `foundry-check` utility with
   ForgeOps. The v1 artifact must have an explicit ForgeOps product identity,
   expose the intended `forgeops` entry point, and make any legacy-tool
   disposition clear without silently changing authority.
2. **Version alignment.** Package metadata, the loaded ForgeOps module,
   provenance, tests, documentation, and the release tag must agree on
   `1.0.0`.
3. **Artifact validation.** CI currently installs from the checkout rather than
   building and testing the exact release wheel. The candidate must build the
   wheel, calculate its checksum, install it in a fresh environment without a
   registry, run provenance and the complete offline command smoke path, and
   retain the candidate artifact for review.
4. **Supported Python proof.** Package metadata declares Python `>=3.11`, while
   current CI proves only Python 3.12. The candidate must either test every
   supported minor version or narrow the declared range to the versions that
   are actually proved. The operator's successful Python 3.14 source
   demonstration is useful evidence but is not an installed-wheel CI matrix.
5. **License and release metadata.** The repository currently contains no
   license file and the wheel contains no license metadata. The accepted MIT
   license and product-specific release metadata must be present in the exact
   candidate artifact.
6. **Release automation and rollback boundary.** A reviewed workflow must
   publish only from the exact approved `forgeops-v*` tag, attach the wheel and
   checksum file to GitHub, use minimal permissions, and avoid PyPI, container,
   deployment, cluster, and endpoint authority. A failed publication must not
   be described as a successful release.
7. **Operator release procedure.** Documentation must cover checksum
   verification, isolated offline installation, provenance, upgrade or clean
   replacement of the pre-v1 local installation, command smoke checks, and
   removal or rollback.

## Deferred or rejected for v1

- model or retrieval integration;
- causal diagnosis, severity, impact, or remediation recommendations;
- one-command collection-to-brief orchestration;
- broader logs, Events, metrics, traces, or arbitrary Kubernetes discovery;
- PyPI publication, container images, package signing, attestations, or a new
  external service;
- cluster deployment, background service operation, persistence, or mutation;
- schema renaming solely to remove `v1alpha1`; package v1 does not claim that
  every artifact schema is a stable v1 API.

Each item remains deferred unless later evidence shows that it directly
improves the final demonstration, proves trustworthiness, or prepares a future
release and receives separate approval.

## Remaining milestone sequence

### Milestone 064 — ForgeOps v1 release-candidate hardening

Purpose: prove trustworthiness and prepare the v1 release. Resolve only the
seven release blockers above, produce a non-published candidate wheel and
checksum, and prove the exact candidate through CI and operator acceptance.

### Milestone 065 — ForgeOps v1 release and closeout

Purpose: complete the v1 release. Reconfirm the exact accepted source and
artifact, create the product-specific tag, publish the GitHub Release wheel and
checksum, verify a fresh operator installation, record limitations, reconcile
documentation, and clean up.

If Milestone 064 cannot prove the candidate, Milestone 065 stops before tag or
publication. Approval authorizes the gates; it does not turn failed evidence
into acceptance.
