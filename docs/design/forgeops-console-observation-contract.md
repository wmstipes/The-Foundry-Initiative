# Console reviewed observation boundary — C5 decision

## Disposition

C5 delivers this design and its operator decision record. It does not deliver
an export button, a validator command, or a new ForgeOps intake. Those require
implementation and acceptance of this contract in a follow-up work package.
The existing Console and ForgeOps v1.0.0 retain their current behavior.

The operator identified three uses: asking for troubleshooting help, preserving
an incident record, and supplying future ForgeOps comparison/briefing. The
preferred investigation order is Pod Events and logs, followed by Service and
EndpointSlice details. This supports designing a reviewed handoff; it does not
prove a repeated workflow benefit, measure time saved, or establish an automated
consumer. See the [exercise record](../guides/forgeops-console-c5-operator-exercise.md).

The later exercise responses also request configuration and connectivity
inspection, plus separately labeled release identity for the running
application and the ForgeOps build that produced a brief. These are follow-up
requirements, not fields of this exact `v1alpha1` candidate. The application
image digest, a package checksum, a release tag, an observation time and a
release date have different meanings. Any future identity display must name
the artifact and hash algorithm, distinguish an unavailable value from a
verified one, and define where its release date and expected digest came from.
Do not silently copy names or image details into this disclosure-limited
observation format or imply that a digest establishes live health or publisher
authenticity.

Decision: design a minimal human-readable handoff and a separate structured
observation artifact. Defer automatic ForgeOps ingestion. Optional diagnostic
excerpts belong in the human handoff only. They must never be implicitly
converted into evaluated ForgeOps checks. The initial implementation candidate
must pass the acceptance matrix below before it can export anything.

## Proposed structured contract

Candidate schema identifier: `forgeops.console-observation/v1alpha1`.
This identifier is reserved by this design, not supported by any existing CLI.
The candidate is an operator-reviewed, untrusted point-in-time observation.
It is not a `forgeops.snapshot/v1alpha1`, health verdict, or authenticated record.

Limits apply before parsing: one UTF-8 JSON document, at most 64 KiB, no BOM,
duplicate keys, non-finite numbers, trailing document, or nesting beyond eight
containers. Unknown fields at every level and unknown schema versions fail
closed. No coercion, implicit defaults, or partial acceptance. All fields in
the following tables are required unless explicitly noted. Integers exclude
booleans. Strings exclude control and Unicode format characters; only diagnostic
text in the separate handoff may contain LF and TAB.

| Top-level field | Exact contract |
| --- | --- |
| `schema` | Literal schema identifier above |
| `createdAtUtc` | Second-precision RFC3339 UTC timestamp, `YYYY-MM-DDTHH:MM:SSZ`; export time, not observation time |
| `source` | Object with exactly `consoleVersion` (1-64 ASCII letters/digits/dot/plus/hyphen), `buildCommit` (40 lowercase hexadecimal characters or null), `mode` (`synthetic` or `live`) |
| `scope` | Object with exactly `contextAlias`, `namespaceAlias` (each matches `[a-z][a-z0-9-]{0,31}`), `generation` (integer 1 through 9007199254740991) |
| `selection` | Array of 1-12 observation objects defined below, ordered by explicit operator selection |
| `review` | Object with exactly `reviewedAtUtc` (same timestamp format), `disclosure` (literal `aliases-and-allowlisted-facts`), `diagnosticsIncluded` (literal false) |
| `limitations` | Exact ordered array: `untrusted-operator-reviewed`, `point-in-time-only`, `not-atomic`, `identity-not-authenticated`, `cause-not-established`, `not-forgeops-snapshot` |

Require every observation timestamp <= review time <= creation time. This is
internal consistency only; clocks and collection statements are not attested.
Forbid mixing contexts, namespaces, generations, or synthetic/live modes in
one artifact. Require fresh review if any selection, alias, field, or content
changes. A scope change discards the staged selection. Different generations
can be retained as separate files, never silently combined.

### Observation object

| Field | Exact contract |
| --- | --- |
| `sequence` | Integer 1-12, contiguous from 1 in array order |
| `kind` | `Pod`, `Service`, or `EndpointSlice` only |
| `resourceAlias` | `[a-z][a-z0-9-]{0,31}`; unique `(kind, resourceAlias)` within the artifact |
| `observedAtUtc` | Timestamp format above; retained from response acquisition, never invented at export |
| `outcome` | `ok`, `empty`, `denied`, `not-found`, `timeout`, `unavailable`, or `stale` |
| `incomplete` | Boolean; true if any collection/projection bound was reached or outcome is not `ok` |
| `facts` | Kind-specific object below for `ok`; otherwise null |

`empty` denotes an explicit attempted read without a selected object; it is
not a healthy result. Missing selection entries mean not supplied, never
negative evidence. Errors contain only the enumerated outcome, with no raw
transport message. A stale result cannot supply facts. An `ok` result can be
incomplete and must retain that flag prominently in the human representation.

| Kind | Exact `facts` fields |
| --- | --- |
| Pod | `phase`: Pending/Running/Succeeded/Failed/Unknown; `readyContainers`, `totalContainers`, `restarts`: integer 0-2147483647 or null |
| Service | `type`: ClusterIP/NodePort/LoadBalancer/ExternalName or null; `ports`: array of 0-8 objects with exactly `protocol` (TCP/UDP/SCTP) and `port` (integer 1-65535); `portsIncomplete`: boolean |
| EndpointSlice | `addressType`: IPv4/IPv6/FQDN or null; `ready`, `notReady`, `unknown`: integer 0-2147483647 or null |

Require readyContainers <= totalContainers when both are known. Null means
not observed, never zero. Any null fact, unknown Pod phase, or truncated ports
requires `incomplete=true`. Port entries must be unique by protocol/port and
sorted by protocol then port. Endpoint readiness counts describe one selected
slice; they cannot be promoted to Service-wide coverage. Names, addresses,
UIDs, selectors, annotations, images, node identities, container names, resource
versions, raw objects, diagnostic text, and activity records are not fields.

The narrow field set supports a basic readiness/routing handoff. It does not
preserve every useful Console relationship or establish why routing failed.
Adding relationship identifiers or diagnostic facts requires a contract revision
and a justified consumer, not an arbitrary extension object.

## Selection, provenance, and disclosure

The core must provide acquisition time and outcome metadata before this
candidate can be implemented honestly. Exporting existing UI data with a newly
invented timestamp is prohibited. Generation is a local session counter; the
same number in two files does not establish a common cluster or session.

Original context, namespace, and resource names stay local. Export requires
explicit aliases and a full preview; suggest neutral aliases, never copy names
by default. Validate aliases but do not claim that validation proves they are
non-sensitive. No original-to-alias lookup table travels in the file. Aliases
are operator assertions and may collide or be reused across unrelated files.
Future before/after use must require an operator-confirmed identity mapping.

Build commit and version are claims, not signatures. A missing build commit is
null and displayed as unknown. A digest can establish exact-byte agreement,
but never author identity, capture authenticity, or chain of custody. Do not
reuse ForgeOps snapshot integrity commands for this unsupported format.

## Human handoff and optional excerpts

The human consumer is a person helping investigate or reviewing an incident.
The proposed renderer produces plain UTF-8 text, at most 96 KiB, with the
structured facts, explicit incompleteness, aliases, collection times, and all
limitations. Include the SHA-256 of the exact companion JSON bytes for pairing
only. Render all imported strings as inert text. No HTML, active links, shell
execution, automatic upload, or clipboard automation is part of this design.

Diagnostic excerpts are optional, excluded by default, and never present in
the structured JSON. A separate human-only section permits at most four
explicitly selected excerpts, at most 4 KiB each and 16 KiB total after UTF-8
encoding. Each has sequence, kind (`log` or `event`), Pod alias, acquisition
time, incompleteness flag, and reviewed text. Logs also retain previous/current
instance choice and a container alias. The handoff lists the operator's
investigation order separately from collection chronology.

Before saving, show every excerpt with an editable review/redaction step and
an explicit acknowledgement that credentials, personal data, addresses, and
internal names may remain. Control-character sanitization is not redaction.
Exceeding any bound blocks export with a request to reduce the selection;
never silently truncate at export. Missing or timed-out log data is represented
as unavailable in the handoff, not reconstructed. No default “include all.”

Log acquisition retains C4's limitation: Pod recreation between validation
and log GET cannot be excluded. Event absence does not prove no Events occurred.
Excerpt metadata must preserve these limits. An excerpt can inform a human
hypothesis but never carry a diagnosis or instruction that software executes.

## Save lifecycle and future consumer

Both representations come from one frozen, reviewed selection. Generate them
only after an explicit save action. A local download remains subject to browser
download-location settings; do not promise a file-picker or controlled retention.
Use neutral filenames without resource identities. No server persistence or
background saving. Failure must be visible and must not claim both files saved
when only one download was initiated. The pairing digest detects a mismatched
companion, not successful disk write or authenticity. Clear staged material on
scope change and explicit clear; the operator owns retained files and deletion.

Before any future consumer evaluates this JSON, it must run a strict offline
validator implementing every rule above. JSON Schema alone is insufficient
for duplicate keys, byte limits, timestamp relations, and ordered sequences.
Errors must identify a field/rule without echoing diagnostic or input content.

For now, the supported ForgeOps workflow remains its own snapshot -> validate
-> compare -> map -> brief pipeline. Do not rename the candidate schema or
synthesize PASS/FAIL checks to bypass that boundary. A future separately
versioned intake needs explicit check semantics, alias identity matching,
missing/truncated handling, and deterministic evaluation. That design is not
accepted merely because the operator wants eventual integration.

## Required implementation acceptance

| Area | Evidence required before shipping |
| --- | --- |
| Strict parsing | Exact/max+1 byte bounds, invalid UTF-8/BOM, duplicate keys at every object depth, unknown fields/schema, invalid enums, bool-as-int, non-finite values, depth, trailing content |
| Semantic validation | Sequence uniqueness/order, count relations, null/incomplete rules, timestamp relations, unsupported kinds, stale facts, mismatched scope/mode |
| Selection lifecycle | Select/review/save, scope-change clearing, late response rejection, edit invalidates review, explicit empty/error states |
| Disclosure | No names/addresses/raw objects in JSON; optional excerpts absent by default, explicit review required, no activity export, no persistence/upload |
| Representation | JSON/text agreement, exact-byte pairing digest, inert hostile text, bounds on excerpts and full output, save failure reporting |
| Compatibility | Existing ForgeOps validates/replays its fixtures unchanged and rejects this distinct format; unsupported intake cannot silently succeed |
| Operator acceptance | Demonstrated help-request and incident-record usability; aligned synthetic before/after exercise before claiming improved investigation or machine evidence integration |

These are future acceptance requirements, not completed C5 tests. C5's executed
validation covers the existing offline pipeline and documentation consistency.

## Follow-on boundaries

Istio is a separate proposed SignalForge learning milestone: first verify
version/ARM64/CNI/resource compatibility, then plan a training namespace,
verification and rollback. No mesh is installed or inspected by C5. A future
mesh plugin needs its own capabilities and typed observation contract; this
schema deliberately contains no arbitrary plugin payload.

ForgeFire remains separately proposed. No fault injection, live collection,
mutation, release, or mesh deployment is authorized by this design.
