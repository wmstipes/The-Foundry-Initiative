# Release identities beside a ForgeOps incident brief — C5 design

## Status and scope

This records the operator's request to see the running application's version,
release date and verifiable hash separately from those of the ForgeOps build
that produced a brief. It is a source contract for a later, explicitly reviewed
display. No existing `forgeops.snapshot/v1alpha1`, incident brief, or proposed
`forgeops.console-observation/v1alpha1` schema has these fields. ForgeOps v1.0.0
and the Console v0.1.0-rc.1 release are immutable. This design does not add
network lookup, release discovery, cluster access or export behavior.

| Label | Version and source | Release date and source | Hash and verification |
| --- | --- | --- | --- |
| Running application | Version returned by a selected, bounded `/version` read, when supplied; display the Deployment's configured image reference and each selected Pod's runtime image identity separately. A tag or `/version` response alone does not establish which bytes ran. | Publication time in an explicitly supplied release record for the **same** identified application artifact. Do not substitute Pod creation, observation, image build or Git commit time. | OCI image manifest/index digest (`sha256:`) when the configured reference is pinned and a runtime image ID can be matched to that exact digest. A tag, URL, image name or digest claim without the runtime match is labeled as a claim, not verified runtime bytes. |
| ForgeOps build producing the brief | `forgeops provenance` module and distribution versions, with execution mode and source path, checked before the brief. An editable/source launch is identified as such. | Publication time in an explicitly supplied release record for the **same** distribution artifact. Do not substitute brief generation time or local file modification time. | SHA-256 of the exact installed/distributed wheel, checked against the reviewed release checksum and asset bytes. Source runs have no wheel identity merely because their module version matches a release. |

An implementation must display the artifact name, source record, observed or
verified state, UTC release timestamp (or explicit unavailable state), digest
algorithm and exact digest scope. An OCI index digest and platform manifest
digest are different bytes; show which one was checked. A wheel hash cannot be
used as a Console executable hash. Console build identity is a third product
identity if a later workflow needs it, and must not be silently labeled
"ForgeOps build."

### Required outcome distinctions

- **Verified bytes:** a selected local/distributed artifact's calculated
  digest matches the supplied expected digest, or a selected runtime image ID
  matches a pinned image digest in the captured Kubernetes evidence. State
  exactly which comparison was performed. This is byte agreement, not publisher
  authentication, running-health proof or chain of custody.
- **Observed claim:** a version endpoint, mutable image tag, manifest label or
  release metadata states an identity that has not been tied to those exact
  runtime/distribution bytes. Show the claim and its source without a verified
  badge.
- **Mismatch:** do not choose one source as authoritative. Show the conflicting
  values and block any combined "verified release" statement.
- **Unavailable:** no exact artifact, digest, release record, runtime image ID
  or defensible version was supplied. Show unavailable for that field; do not
  infer a date or hash from another product's artifact.

The structured incident brief currently summarizes validated before/after
snapshots and an informational mapping. It should remain reproducible from
those inputs. A future display needs a separately versioned, strictly validated
identity input (or a separately reviewed brief-schema revision), explicit
before/after association for the application, offline operation, exact-byte
pairing and missing/mismatch semantics. It must not invent health checks,
import Console activity, expose credentials or mutate ForgeOps v1.0.0 to accept
unsupported data. The operator must review release records before relying on
publisher claims. No release identity is asserted by the aligned synthetic
Console exercise; its image names and logs are demonstrative.

The current ForgeOps v1.0.0 [release record](../milestones/milestone-065-forgeops-v1-release-and-closeout.md)
contains a wheel SHA-256 and source tag; the [provenance command](../guides/forgeops-incident-copilot-demonstration.md#prepare-the-exact-checkout)
identifies execution mode. These are distinct checks. The Console
[engineering preview](../releases/forgeops-console-v0.1.0-rc.1.md) has its own
archive hash and must not be presented as the ForgeOps wheel or the running
Restaurant API image.
