# ForgeOps Console v0.1.0-rc.1 — Windows engineering preview

This is the first public Console prerelease, separate from ForgeOps v1.0.0.
It is an unsigned engineering preview, not a general production-support claim.

## Exact package

- Tag: `forgeops-console-v0.1.0-rc.1`.
- Source: `af0f3ec54d842c876e63ccc6cba9c7029756d2f0`.
- Build: [Required Validation run 35768592178](https://github.com/wmstipes/The-Foundry-Initiative/actions/runs/35768592178).
- Download: `forgeops-console-candidate-af0f3ec54d84-windows-amd64.zip`.
- SHA-256: `037841539937826dc3f6094bc3fcbf29529bb4ea17948e69d94ee11246f2d801`.

The accepted archive is published unchanged. Its candidate filename, manifest
status and packaged README are intentional historical build metadata.
These release notes state the later, narrowly scoped prerelease decision.
The tag identifies the actual build source, not the later documentation commit.
Download the named Windows ZIP, not GitHub's automatically generated source archives.

## What it provides

A local, loopback-only Kubernetes resource browser with three compiled
first-party plugins: example, resources and diagnostics. It requires one explicit
kubeconfig and paired browser assets. Resource reads are bounded, context changes
invalidate older work, and diagnostics are snapshots. Command previews are
explanations only; no commands are executed.

Keep both executables and the complete `web` directory together. Start the
synthetic demo from the extracted folder:

```powershell
.\forgeops-console-demo.exe --web-dir .\web --listen 127.0.0.1:9090
```

Open http://127.0.0.1:9090. Production use requires the separate
`forgeops-console.exe` entrypoint and an explicit `--kubeconfig` path;
consult the packaged README before using credentials.

## Tested scope

- Windows 11 Pro 25H2, build 26200.9457, x64.
- Microsoft Edge 153.0.4234.48, 64-bit.
- Keyboard/focus, 200% zoom, narrow-window layout and a focused Windows Narrator
  walkthrough of scope, resource selection/details and diagnostics preview.
- Installed integrity/identity, loopback/nonce boundaries, synthetic reads,
  mismatched-pair rejection and restoration; operator Ctrl+C shutdown.
- Real SignalForge namespace discovery and Pod/Service reads in
  `forge-restaurant`, including clearing the previous resource selection.

The live check did not re-measure the Kubernetes server version or exercise
live logs/Events. Historical SignalForge v1.36.4 records are not a compatibility
range. Linux amd64 has native CI evidence but is not an asset in this first
Windows preview. No macOS, arm64, EKS or service-mesh acceptance is claimed.

## Security and limitations

Packages are unsigned and lack publisher attestation. Checksums identify bytes,
not publisher authenticity. Use the assets from this repository's release.
Smart App Control may block unsigned software; do not bypass it. An earlier
local Go test executable was blocked, while hosted Windows tests and this
installed package passed. That development-test limitation remains disclosed.

The client rejects external authentication plugins, secondary credential files,
proxies and insecure TLS; standard EKS exec-based kubeconfigs are unsupported.
The application's read-only routes do not reduce the supplied credential's
Kubernetes permissions. Logs and Events may contain sensitive application data
and are not guaranteed redacted. Trusted first-party plugins are not sandboxed.

The 2026-09-22 review recorded no findings from govulncheck v1.8.0 and production
npm audit on the same application source and dependency locks. This is
point-in-time evidence, not a guarantee against vulnerabilities.
No comprehensive accessibility conformance is claimed.

There is no export/intake integration, persistent session storage, third-party
plugin loader, cluster deployment or Kubernetes write operation.

## Recovery and removal

Stop Console with Ctrl+C. Restore only a complete executable/browser pair.
This first Console release has no historical Console predecessor to roll back
to; same-pair restoration was tested. To remove it, stop it and delete its
extracted directory, leaving your separately stored kubeconfig untouched.

[Acceptance record](https://github.com/wmstipes/The-Foundry-Initiative/blob/50e0f4319a749de255093276da3139bdf79e16ca/docs/milestones/forgeops-console-c7-release-readiness.md)
