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
| 1 — Scope and support | Separate candidate targets from supported OS/browser/Kubernetes claims; record exclusions | Narrow Windows engineering preview scope approved; see final decision below |
| 2 — Security and dependencies | Audit credential, loopback and plugin boundaries; locked dependencies and notices; review vulnerability results | Exact-source dependency review reconciled on 2026-09-22; limitations retained |
| 3 — Candidate packaging | Build committed source, pair both executables/browser, identify exact inputs and hash packaged bytes | Native builder and informational `--build-info` implemented; unsigned, no publisher attestation |
| 4 — Installed acceptance and rollback | Execute extracted files outside checkout, reject damaged pairs, restore complete pair; operator checks exact archive | Automated verifier and Windows synthetic/live UI/Ctrl+C checks passed on 2026-09-22; historical-release rollback is not applicable to the first Console release (see disposition below) |
| 5 — Usability and accessibility | Labels, native semantics, keyboard focus and responsive layout checked; operator keyboard/zoom/screen-reader evidence | Edge keyboard/focus, zoom/narrow-window and focused Narrator checks passed; no accessibility conformance claim |
| 6 — Review and release decision | Review PR checks, exact candidate hashes, support matrix and unresolved risks; publish only accepted assets | Windows v0.1.0-rc.1 prerelease approved; exact-asset publication and verification pending |

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
| Mike's Windows laptop | C7 packaged verifier and five manual checks passed for run 35768592178. The earlier C6 resources-test Application Control block remains unresolved |
| Browser | Microsoft Edge 153.0.4234.48 (Official build), 64-bit: exact-archive keyboard/focus, zoom and narrow-window checks passed; focused Narrator walkthrough passed |
| Kubernetes | client-go v0.36.4 pinned; exact C7 Windows candidate passed bounded SignalForge live reads; server version was not re-measured in this check and no compatibility range is claimed |
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
The laptop resources test remains blocked, not passed. For a narrowly scoped
engineering preview, this is a disclosed development-test limitation rather
than evidence of a shipped runtime failure: hosted native Windows tests and
the installed laptop candidate passed. No blanket Windows or application-control
policy compatibility is claimed, and no security-control bypass is prescribed.

Live compatibility testing requires an explicitly selected cluster and bounded
read scope. The operator subsequently supplied the SignalForge target and
completed the installed-candidate walkthrough recorded below. Automated
verification remains synthetic-only; the assistant performed no cluster operation. C5 export and aligned operator acceptance remain
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
The earlier release hold is superseded only for the narrow Windows preview by
the final decision below. Broader support remains unestablished.

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

## Packaged Windows operator acceptance — 2026-09-22

The operator supplied terminal output and confirmed all five requested manual
checks passed without errors. This is operator-observed laptop evidence,
separate from hosted CI and the earlier source-built C6 demo.

- Source revision: `af0f3ec54d842c876e63ccc6cba9c7029756d2f0`.
- Successful main Required Validation run: [35768592178](https://github.com/wmstipes/The-Foundry-Initiative/actions/runs/35768592178).
- Windows artifact: `forgeops-console-candidate-windows-latest`, ID
  `10713232162`; inner archive
  `forgeops-console-candidate-af0f3ec54d84-windows-amd64.zip`.
- Browser: Microsoft Edge `153.0.4234.48` (Official build), 64-bit.
- OS: Windows 11 Pro, version 25H2, build `26200.9457`, x64 (operator screenshot).
- Inner ZIP SHA-256, supplied by the operator using `Get-FileHash`:
  `037841539937826dc3f6094bc3fcbf29529bb4ea17948e69d94ee11246f2d801`.

The supplied command block checks the inner archive against its adjacent
SHA256SUMS before running the verifier and stops on failure. The terminal
output reports PASS for archive integrity, installed identity, loopback/nonce
boundaries, synthetic reads, production offline bootstrap, mismatched-pair
rejection and restoration. The operator subsequently supplied the inner ZIP
digest above. It is distinct from the GitHub outer artifact digest; the assistant
did not independently rehash the laptop archive.

| Manual check on the extracted candidate | Operator result |
| --- | --- |
| Synthetic banner, context activation and signalforge namespace selection | Passed, no errors |
| Pod/Service transitions clear previous rows and selection | Passed, no errors |
| Tab/Shift+Tab/Enter navigation and visible focus | Passed, no errors |
| Readability at 200% zoom and in a narrow window | Passed, no errors |
| Ctrl+C returns promptly to PowerShell | Passed, no errors; terminal prompt shown |

The verifier's LIMIT line describes its own forced Windows process cleanup.
It is not a failed check. The separate operator Ctrl+C result supplies manual
shutdown evidence for this exact candidate; it does not turn forced automated
termination into graceful-shutdown coverage.

This initial exercise accepted bounded synthetic Windows/Edge behavior.
Production bootstrap in the automated verifier used only synthetic configuration.
The subsequent operator live and Narrator checks below extend that evidence;
they do not change the verifier's coverage.

## Live and Narrator operator acceptance — 2026-09-22

The operator used the same installed Windows candidate from run 35768592178,
then reported all live checks completed successfully with no errors.

- Explicit configuration: `%USERPROFILE%\.kube\config-signalforge`.
- Context: `kubernetes-admin@kubernetes`; namespace: `forge-restaurant`.
- Production banner, context activation and namespace discovery: passed.
- Pod listing and selected details, then Service listing with the previous Pod
  selection cleared: passed.
- Ctrl+C returned promptly to PowerShell: passed.

This is real-cluster read acceptance for the selected SignalForge environment.
The credential is an administrator identity; Console's read-only operation set
does not reduce its Kubernetes permissions. No cluster writes, live logs or
Events were requested in this walkthrough. The server version was not captured
again, so the historical v1.36.4 record is not promoted to a fresh version check.
No credential contents were supplied to the assistant.

The operator then returned to the synthetic demo in Edge and reported each
focused Windows Narrator area passed:

| Spoken-output area | Operator result |
| --- | --- |
| Context/namespace labels, values and scope controls | Passed |
| Pod name, selected state and reading object details | Passed |
| Diagnostics checkbox/container/buttons and reading the Events command preview | Passed |

These results are separate from the earlier 200% zoom/narrow-window checks.
They establish a focused Narrator usability walkthrough, not comprehensive
screen-reader coverage or accessibility-standard conformance. No new automated
test was added for these operator observations.

## First-release disposition and remaining release work

Historical Console release rollback is **not applicable** to the first Console
release: the existing ForgeOps v1.0.0 release is a separate product, not an older
Console package. Keep the passed complete-pair restoration evidence and the
documented stop/remove procedure. Do not claim that historical rollback or
manual removal was tested. A later Console upgrade must evaluate rollback to
its actual predecessor.

The earlier local Application Control block remains an unresolved source-test
execution limitation. It does not negate the successful installed candidate.
Any initial preview must retain the unsigned-package and narrowly tested
environment disclosures; broad Windows support remains unestablished.

No repeat of accepted operator checks is required for documentation changes.
The following final decision resolves the remaining scope/dependency review.
This record does not itself publish assets or certify untested environments.

## Final prerelease decision — 2026-09-22

The operator approved the narrowly scoped Windows engineering prerelease.
Disposition: **GO for preparation and publication of the exact accepted Windows
archive; publication not yet verified**.

- Version/tag: `forgeops-console-v0.1.0-rc.1`, marked prerelease and not Latest.
- Tag target: accepted source `af0f3ec54d842c876e63ccc6cba9c7029756d2f0`,
  not a later documentation-only main commit.
- Assets: the unchanged accepted Windows ZIP and a SHA256SUMS file containing
  its recorded digest. Linux remains CI-validated and is not published here.
- Tested environment and limitations: the Windows/Edge/Narrator and SignalForge
  observations above; no broad OS, Kubernetes or accessibility support claim.
- Security review: PR #110 records govulncheck v1.8.0 with no findings and
  production npm audit with zero vulnerabilities on 2026-09-22. Comparison of
  reviewed source `916c9d747153b8058661444007f98a7c70a229cf` with the accepted
  candidate shows only workflow, verifier and documentation changes; application
  source and Go/npm dependency locks are unchanged. These results are applicable
  point-in-time evidence, not a new scan or a vulnerability guarantee.
- Required Validation run 35768592178 passed for the exact accepted source.
  Subsequent acceptance-record changes are documentation only.
- The assistant could retrieve the artifact reference, but the download URL
  returned HTTP 403, so it did not independently rehash the archive. The
  publication procedure checks the operator's archive against the recorded
  digest, then downloads and verifies draft assets before publishing.

The accepted ZIP's candidate label and historical packaged release-hold text
remain unchanged to preserve its identity. The scoped release notes explain
the later prerelease decision; this does not turn the package into a generally
supported stable release.

See [release notes](../releases/forgeops-console-v0.1.0-rc.1.md) and
[publication procedure](../releases/forgeops-console-v0.1.0-rc.1-publish.md).
Publication completion requires the actual release URL, prerelease state,
tag target and asset evidence; do not infer completion from this PR's merge.
