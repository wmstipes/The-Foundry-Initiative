# ForgeOps Console C4 — bounded Pod diagnostics

## Approval and scope

The operator approved C4 and all related gates after C3 live reconciliation
merged through PR #102 at `d807919e9f388b7aeb93338e853de2565c3d6a0c`.
C4 improves the demonstration by connecting a selected Pod to bounded logs,
Events, and command explanation without executing commands or expanding
ForgeOps v1.0.0 evidence authority.

This implementation is a candidate pending published CI, PR review, and merge.
Live log/Event access requires separate authorization; none was performed during
implementation. C3's approved resource reads do not authorize these new data.

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

## Gates

1. Contract and disclosure bounds — approved and implemented as above.
2. Core capabilities and lifecycle — implemented; offline tests passed.
3. Compiled plugin and UI — implemented; DOM/API tests and synthetic smoke passed.
4. Adversarial, cancellation, race, and build validation — local checks passed.
5. Documentation, publication, CI, and review — pending.
6. Merge and reconciliation — pending operator review/merge; no release or
   deployment implied. A live check remains separately authorized.

## Deferred work

- Continuous follow, Event watch, downloads, and broader resource Events.
- C3-UX-01 scheduling-label clarification remains open; this C4 change does not
  silently close or implement that separately tracked usability follow-up.
- C5 evidence integration and C6/C7 distribution/release remain separately gated.
