# Milestone and acceptance records

These are dated evidence records. Use [project status](../project-status.md)
and the [operations index](../runbooks/README.md) for present-day guidance.
Older versions, test totals, planned next steps, and commands remain part of
their original history unless a subsequent-outcome note says otherwise.

## Recent platform work

| Record | Outcome and boundary |
| --- | --- |
| [Identity preservation and recovery](identity-preservation-recovery-2026-09-29.md) | Installed kubeadm inputs reproduce the reviewed candidate; off-node copies and offline reconstruction verified; full identity recovery remains open |
| [Private access and Headlamp OIDC](private-access-and-headlamp-oidc.md) | September 28 protected-service and interactive identity acceptance; subsequent preservation evidence is recorded above |
| [Documentation review](documentation-review-2026-09-28.md) | Cross-repository Markdown, current operations, test inventory, and Wiki reconciliation |
| [Loki recovery](loki-recovery-candidate.md) | Cold backup, restart persistence, isolated restore and cleanup accepted; retention remains open |
| [Central logging preflight](central-logging-preflight.md) | Historical storage/design record; current logging procedure is in the component runbook |
| [Istio admission](istio-admission-review.md) and [control-plane checkpoint](istio-minimal-offline-review.md) | Historical decisions leading to the active [learning lab](../../k8s/istio-lab/README.md) |

## Numbered workstreams

- The [main roadmap](../../ROADMAP.md) indexes completed SignalForge and
  ForgeOps milestones 001-030 and 032-065. No Milestone 031 record exists in
  this repository; this review does not invent one or renumber the sequence.
- [ForgeOps post-v1 milestones 066-088](../roadmaps/forgeops-post-v1-roadmap.md)
  are proposed future work, not completed implementation records.
- Console has its own [C1-C7 roadmap](../roadmaps/forgeops-console-roadmap.md)
  and records in this directory. C5 export/intake is still design-only;
  [C7](forgeops-console-c7-release-readiness.md) records the accepted Windows
  preview, distinct from the later cluster pilot.
- Workbench's [W1-W7 roadmap](../roadmaps/forge-yaml-workbench-security-guidance-roadmap.md)
  is independent of the completed Workbench 032-042 sequence.

Use a named record for platform work that does not belong to those numbered
sequences. Record the date, scope, source of live evidence, changes, result,
rollback evidence and remaining limits. A new document does not imply a new
release, deployment, or accepted recovery test.
