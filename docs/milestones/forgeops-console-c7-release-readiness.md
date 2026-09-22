# Console C7 — release readiness and release decision

## Authorization and scope — 2026-09-22

The operator approved C7 and all its gates after C6 closeout PR #109 merged at
`10e6e6178759866c2ae8ccd81a7f1f93e253a8fa`. That approval authorizes execution of
the work; it is not evidence that release criteria have passed. C7 prepares
an independently identified Console candidate without changing ForgeOps v1.0.0.

Retain the three compiled first-party plugins and the explicit-kubeconfig,
loopback-only, bounded read-only model. No authentication adapter, third-party
loader, exporter, persistence, container, or cluster deployment is admitted.
Candidate targets are native Linux amd64 and Windows amd64. Public support
and version selection follow acceptance rather than the existing development
package label. A public release is held when evidence is incomplete.

## Gates and disposition

| Gate | Exit evidence | Current disposition |
| --- | --- | --- |
| 1 — Scope and support | Separate candidate targets from supported OS/browser/Kubernetes claims; record exclusions | Defined below; no public support claim |
| 2 — Security and dependencies | Audit credential, loopback and plugin boundaries; locked dependencies and notices; review vulnerability results | Existing protections inspected; installed boundary checks added; final release security review remains open |
| 3 — Candidate packaging | Build committed source, pair both executables/browser, identify exact inputs and hash packaged bytes | Native builder and informational `--build-info` implemented; unsigned, no publisher attestation |
| 4 — Installed acceptance and rollback | Execute extracted files outside checkout, reject damaged pairs, restore complete pair; operator checks exact archive | Automated verifier implemented; exact-archive Windows UI/Ctrl+C and historical-pair rollback remain open |
| 5 — Usability and accessibility | Labels, native semantics, keyboard focus and responsive layout checked; operator keyboard/zoom/screen-reader evidence | Concrete source issues corrected; browser assistive-technology acceptance remains open |
| 6 — Review and release decision | Review PR checks, exact candidate hashes, support matrix and unresolved risks; publish only accepted assets | Candidate review; public version, tag and release held pending evidence |

## Architecture and security assessment

The core already rejects non-loopback listen addresses, mismatched Host/Origin,
and nonce-free operation requests. The credential loader takes one explicit
regular file with a 1 MiB cap and no ambient/in-cluster discovery. The live
factory rejects active/external credential mechanisms, insecure TLS and proxies.
Existing Go tests cover these paths. The candidate verifier repeats representative
checks through the installed HTTP process and checks that a synthetic token
canary is absent from production bootstrap without activating any context.
This canary check is not proof that all possible credential leaks are impossible.

Capabilities are fixed to compiled identities/routes and declared handlers;
in-process Go code and same-origin browser modules are not isolated. Existing
scope-generation, cancellation, output bounds, CSP and no-store defenses remain.
Application-authored logs/Events can contain secrets despite sanitized transport
errors. A local hostile process, modified asset directory or compromised build
chain is outside source fingerprint protection. Checksums and embedded commit
metadata are not signatures. No general third-party plugin scope is justified.

Go and npm versions/dependencies are recorded; source locks are retained and
Go builds use `-mod=readonly`. Notice collection and inventories improve package
review but do not claim a complete SBOM, vulnerability clearance or legal audit.
Dependabot previously omitted Console; C7 adds its Go and browser ecosystems
with separate security updates and patch-only version groups. Existing CI
security checks remain required. A fresh release security review
must consider the candidate's exact dependency graph and current findings.

## Packaging and independent verification

`build-forgeops-console-candidate.py` requires committed tracked changes and
stages only explicitly selected Git inputs into a temporary source tree. It
builds native targets with CGO disabled and no ambient cross-compilation flags,
then writes one ZIP and SHA256SUMS into a new directory. No existing build
output, credentials or runtime activity enter the package. Timestamps and ZIP
ordering are fixed; cross-machine bit-for-bit reproducibility is not claimed.

The manifest identifies source commit/tree, tool versions, OS/architecture,
source-pair fingerprint and each payload file's SHA-256. Both executables expose
`--build-info` before loading configuration or starting a listener. The verifier
checks that identity against the manifest, so accidentally mixed executables
cannot pass merely because the archive has an updated outer checksum.

Archive verification is bounded and rejects traversal, symlinks, duplicate or
case-colliding entries, unsafe Windows names, undeclared files, missing runtime
files, and hash mismatches before extraction/execution. It accepts an explicitly
provided expected digest; authenticity still depends on the source of that
digest. It is intended for reviewed project candidates, not arbitrary software.

The installed rehearsal uses an unrelated working directory. It validates the
demo and production bootstrap with synthetic-only inputs, loopback/nonce
boundaries, a deliberately mismatched browser manifest, then restoration of a
saved complete pair. Windows automated termination is forced cleanup, not
Ctrl+C evidence. Historical-release rollback remains distinct from this
same-pair restoration check.

## Support evidence and remaining operator work

| Environment or behavior | Evidence / limit |
| --- | --- |
| Linux amd64 | Source checks and native extracted-candidate rehearsal; distro-specific public support remains undecided |
| Windows amd64 CI | Native tests/build/installed rehearsal required by the matrix; no Smart App Control policy equivalence claimed |
| Mike's Windows laptop | C6 source-built demo passed; resources test executable was blocked by Application Control with Smart App Control On. C7 archive is a new acceptance target |
| Browser | Native list semantics, current/pressed state, visible focus and intermediate-width layout improved; exact-archive keyboard/zoom and screen-reader review pending |
| Kubernetes | client-go v0.36.4 pinned; historical SignalForge v1.36.4 walkthroughs are context, not a public compatibility range or C7 live acceptance |
| EKS, macOS, arm64, mesh | Not accepted or exercised in this candidate |

The misleading Node `Scheduling` boolean now reads `Unschedulable (cordoned)`;
true describes the actual stored flag, not an assertion that a Pod can schedule.
The resource list now uses native list items and exposes selection to assistive
technology. These changes address observed code-level issues; they do not
certify accessibility or close the manual checks.

After CI and merge, download the native candidate for the exact reviewed commit,
verify its SHA-256, and use the packaged README's synthetic keyboard/zoom and
Ctrl+C checks. Record archive digest, OS/browser versions and failures. A policy
block is a blocked result, never a passing test; do not bypass Windows controls.
If the laptop resources suite remains blocked, public Windows support stays
conditional on a reviewed resolution and execution of that suite.

Live compatibility testing needs an explicitly selected cluster and bounded
read scope. This work performs no cluster operation. C7 approval does not supply
credentials or identify a live target; use synthetic fixtures until those
concrete inputs are available. C5 export and aligned operator acceptance remain
separate and must not be advertised as delivered.

## Validation record

Six new Python tests address archive tampering and extraction gaps. They are
not tests of milestone prose. One Go regression test covers the Node flag for both boolean values (55 Go
test functions total); the 19-case Vitest inventory is unchanged.
Native CI runs the existing Go suite on Linux and Windows and runs the installed
candidate rehearsal after browser validation. Candidate archives are retained
as CI artifacts, with read-only repository permissions and no release job.

Local Linux evidence: all 254 top-level Python tests and all 19 Vitest cases
passed; the Go race suite and vet passed before the final isolated label test,
which also passed. Production npm audit reported zero vulnerabilities. The
native archive built successfully and passed installed verification (both
entry-point identities, denied requests, synthetic reads, mismatch and restore).
Workflow YAML parsing, relative documentation links and whitespace checks passed.
Native Windows results must come from the PR matrix; they are not inferred from
Linux execution. PR checks/merge and operator archive acceptance remain separate.

See [testing and validation](../testing-and-validation.md) and the
[packaged candidate instructions](../releases/forgeops-console-candidate.md).
The release decision remains **HOLD** until the remaining gate evidence above
is recorded; approved work may continue without treating missing evidence as
an additional permission request.

## Post-merge validation follow-up — 2026-09-22

PR #110 merged at `10cad54be5aafc89554467e3f9d89a67b1d8c9d5` after green
PR checks. Main run 35764635209 then failed in Windows installed production
verification: a denial request received WinError 10054 instead of a readable
403 response. Both executables had built, and the other main validation jobs
passed. The original log did not identify which of the three denial probes
reset; this is a transport failure, not evidence that an unauthorized request
was accepted.

The verifier previously sent an unnecessary JSON body to the bodyless activity
endpoint. It now sends an explicit empty POST for the nonce check, avoiding
that early-rejection/body timing path, closes error responses, and identifies
Host/Origin/nonce in any subsequent failure. The requirement remains exactly
HTTP 403; resets and timeouts still fail. No application authorization check,
security policy or test gate is weakened. Existing native installed rehearsals
provide the relevant regression check; no extra prose tests are added.

Dependabot's separate Kubernetes v0.37.0 PRs are not merged acceptance: PR #111
hits the existing v0.36.4 policy assertion; PR #112 mixes module versions and
fails compilation. Its attempt to update k8s.io/api alone also failed dependency
resolution. Patch-only grouping does not prohibit individual minor/major PRs.
Keep the accepted module set until a coordinated update is reviewed separately.
