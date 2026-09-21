# ForgeOps Console C4 — bounded Pod diagnostics

## Approval and scope

The operator approved C4 and all related gates after C3 live reconciliation
merged through PR #102 at `d807919e9f388b7aeb93338e853de2565c3d6a0c`.
C4 improves the demonstration by connecting a selected Pod to bounded logs,
Events, and command explanation without executing commands or expanding
ForgeOps v1.0.0 evidence authority.

The implementation is accepted through PR #103 at
`7910f0a4e9cb66e4e54014cfbf9d817181401ec2`. Live log/Event access required
separate authorization and was not performed during implementation. The later
authorized walkthrough is recorded below; it grants no ongoing live authority.

## Implemented contract

The compiled `forge.diagnostics` plugin declares `pods.logs.read`, `events.read`,
and `command.preview`. One nonce-protected POST route maps exact operations to
those capabilities; the broker rejects cross-capability dispatch. Requests have
only generation, operation, Pod, optional container/previous, and preview target.
Unknown JSON fields, extra URL query data, unknown operations, and invalid names
fail closed. Context and namespace come exclusively from the core session.

| Operation | Fixed behavior and limits |
| --- | --- |
| Logs | Typed Pod GET validates the selected regular/init container; typed Pod log GET uses explicit container, previous boolean, follow=false, tail=500, limitBytes=65536. Browser offers regular containers only. |
| Events | Typed Pod GET obtains current UID; namespace-scoped core/v1 Event list uses core-built Pod UID/name/kind/namespace selectors, and repeats the match before projection. |
| Preview | Offline deterministic PowerShell and POSIX quoting from validated structured selections; manual kubeconfig placeholder; labeled not executed and not an exact equivalent. No cluster request or existence/permission claim. |
| Request budget | Five seconds, two diagnostics at once in addition to four resource-query slots; busy returns 429. No follow, watch, background polling, or retry loop. |
| Content budget | 64 KiB / 500 log lines; 100 Events; Event name/type/reason/message bounded to 253/32/128/1024 bytes; 256 KiB encoded response. Pagination and reached bounds mark incompleteness; oversized serialized output fails closed. |
| Lifecycle | Request cancellation and scope changes close the upstream stream; timeouts/disconnections discard partial text. UI AbortController and request identity reject late results; changing Pod/scope unmounts and clears content. Namespace generation validation and selection use one lock. |
| Activity | Existing 100-entry memory-only activity list receives capability, scope, outcome, count and truncation, never log/Event bodies or preview text. |

## Disclosure and limits

Logs and Event messages may contain credentials or personal data. The warning
requires acknowledgement before UI reads, but is not a redaction guarantee or
an authorization mechanism. Kubeconfig material, raw Pod/Event objects,
annotations, transport errors, and arbitrary client access are not returned.
Unsafe control/format characters are replaced, invalid UTF-8 is normalized, and
React renders content as inert text. No export, clipboard automation, shell,
mutation, exec, attach, proxy, port-forward, or persistent storage is added.

The typed SDK can allocate an upstream Event response before projection; the
documented byte bounds concern delivered projections, not a global process
memory guarantee. Readiness and Event counts are point-in-time observations.
Pod log GET has no UID precondition: Pod recreation between validation and the
log request cannot be excluded. Event previews are name-scoped, whereas actual
Console Event reads additionally enforce current UID. Preview text explicitly
explains that projection, sanitization, cancellation, and generation semantics
have no exact kubectl equivalent. No Windows shell execution is tested or used.

## Validation

Offline tests cover fixed typed GET mappings, invalid request/container/scope,
forbidden/unauthenticated/not-found/unavailable errors, disconnected streams,
timeout, explicit cancellation, scope-change cancellation, concurrency recovery,
byte/line/Event/serialized limits, control characters and invalid UTF-8,
metadata-only activity, offline quoting, and cross-capability denial.

Browser DOM/API tests cover warning/container gating, text-only rendering,
cancellation with late results, generation-change unmount, stale scope rejection,
error/truncation/preview states, nonce transport and AbortSignal propagation.
They are automated DOM tests, not a live browser/cluster acceptance claim.

The synthetic demo adds hard-coded log and Event data and remains permanently
labeled synthetic, with no kubeconfig loading or live factory. Suite counts and
final execution results are reconciled in `docs/testing-and-validation.md`.
All 47 Go test functions pass with race detection; vet, formatting, locked tidy,
and both entry-point builds (Linux and Windows/AMD64 cross-build) pass.
The cross-build does not establish Windows runtime acceptance.
All 12 Vitest cases, browser build, and
zero-vulnerability production audit pass. Python validation passes 248 top-level
unittest cases and 257 full-discovery pytest cases. A synthetic loopback HTTP
smoke passed log/Event reads, offline preview, metadata activity, no-store headers,
and stale-generation rejection. No live cluster was used.

## Published acceptance

Published head `35005f9008a9a184fa1c9f34fa29109a3c64c67d`, locally tested commit
`75a95719c19a5c9f03e9fd6bc8577b344984b20b`, and the PR #103 merge share tree
`1f5a19908a1727c335a451cedf1b8c7d0bb4bdbe`.
The published-head PR workflows completed successfully:

- Required Validation: `35647386610`.
- Repository Security Validation: `35647386668`.
- ForgeOps CI: `35647386714`.

The operator separately reported green post-merge workflows. The connector's
workflow query verifies PR-triggered runs, not independent post-merge runs.

## Bounded live walkthrough — 2026-09-21

After explicit authorization, the operator used the production Console on the
Windows laptop at merged source `7910f0a4e9cb66e4e54014cfbf9d817181401ec2`.
Terminal output confirmed all 12 Vitest cases, the web production build, all Go
package tests, and the production Go build passed; npm installation reported
zero vulnerabilities. These repeat runs do not increase suite counts or prove
Windows race-detector acceptance.

The server used an explicit existing kubeconfig and loopback `127.0.0.1:9090`.
The selected context was `kubernetes-admin@kubernetes`, namespace
`forge-restaurant`, Pod `restaurant-api-6dfbf8dd9b-4nnlb`, and container
`restaurant-api`. The context name does not establish least-privilege RBAC.
Evidence was operator-supplied screenshots, terminal output, and confirmation,
not an independently executed audit or signed runtime provenance record.

| Check | Observed result |
| --- | --- |
| Read controls | Sensitive-data warning acknowledged; log controls unavailable before explicit container selection; previous-instance option unchecked. |
| Current logs | Snapshot displayed with the safety-limit/incompleteness warning. The exact triggering bound was not determined from the screenshot. |
| Pod Events | Request completed with no matching Events; the UI explicitly avoided claiming no Events had occurred. |
| Log preview | Both shell variants displayed the selected context, namespace, Pod and container; tail 500, limit 65536 bytes, timeout 5s, follow=false, previous=false, and manual kubeconfig placeholder. |
| Event preview | Both shell variants displayed the selected scope and Pod name/kind selector with timeout 5s; the UI explained the actual read's additional UID matching. |
| Preview authority | Both were labeled explanation only / not executed, with non-equivalence and permission caveats; no preview command was executed. |
| Clear and reset | Operator confirmed Clear diagnostics removed the preview, regeneration worked, and reactivating the same context cleared the namespace and removed the diagnostics panel. |
| Shutdown | Operator explicitly confirmed the Console stopped after the walkthrough. |

Disposition: bounded current-log/Event and preview happy paths plus visible
clearing/reset passed. No previous-container read, in-flight cancellation,
hostile-data injection, error-path exhaustion, network-reachability validation,
or cluster mutation was part of this live check. Synthetic/unit evidence for
those implemented boundaries remains separate. No raw log/Event text,
screenshots, private addresses from log contents, or credential files are
published in this closeout.

## Gates

1. Contract and disclosure bounds — approved and implemented as above.
2. Core capabilities and lifecycle — implemented; offline tests passed.
3. Compiled plugin and UI — implemented; DOM/API tests and synthetic smoke passed.
4. Adversarial, cancellation, race, and build validation — local checks passed.
5. Documentation, publication, CI, and review — implementation accepted through
   PR #103 with the successful published workflow runs above.
6. Merge and reconciliation — implementation merged; authorized live walkthrough
   and shutdown confirmed. This documentation-only closeout awaits its own
   review/merge. No release, deployment, or ongoing live access is implied.

## Deferred work

- Continuous follow, Event watch, downloads, and broader resource Events.
- C3-UX-01 scheduling-label clarification remains open; this C4 change does not
  silently close or implement that separately tracked usability follow-up.
- C5 evidence integration and C6/C7 distribution/release remain separately gated.
