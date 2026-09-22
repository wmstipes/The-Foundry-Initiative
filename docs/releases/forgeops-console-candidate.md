# ForgeOps Console C7 candidate

This is an unsigned engineering candidate, not a supported public release.
Its identity is the full source commit in `manifest.json`, not the frontend
package's `0.1.0` development label. ForgeOps v1.0.0 is a separate product.

## Contents and trust

Keep both executables and the complete `web` directory together. `manifest.json`
records the commit, Git tree, target, tool versions, source-pair identity, and
SHA-256 of every other packaged file. The adjacent `SHA256SUMS.txt` covers the
archive. Checksums detect changed bytes relative to an expected value; they do
not authenticate a publisher. Obtain the archive and expected digest from the
reviewed CI run for the exact PR commit. No signing or attestation is supplied.

The build stages committed files only, runs locked dependency installation,
and includes repository/Go/dependency license notices plus dependency inventories.
This is not an SBOM completeness or legal-compliance certification. No kubeconfig,
user settings, local executable, logs, or diagnostic snapshots are packaged.
The read-only loopback model assumes a trusted local user and asset directory;
a local process with equivalent authority can still access or replace files.

## Candidate environments

Native Linux amd64 and Windows amd64 packages are built and exercised in CI.
A green runner is not a promise of support for every Linux distribution,
Windows application-control policy, browser, or Kubernetes server. macOS,
Linux arm64/Raspberry Pi binaries, containers, and in-cluster deployment are
not candidate targets. There is no public Kubernetes compatibility matrix yet.
The client library is pinned to client-go v0.36.4; that alone does not prove
server compatibility. C3/C4 historical SignalForge walkthroughs used Kubernetes
v1.36.4 and do not replace acceptance of this installed candidate.

Windows Smart App Control may block these unsigned executables or Go test
binaries. Stop and record that result. Do not disable application control,
add blanket exclusions, or relocate files to evade a policy. C6's laptop
resources suite remains blocked even if CI's Windows suite passes.

## Start without cluster access

Extract into a new directory. From that directory on Windows PowerShell:

```powershell
.\forgeops-console-demo.exe --build-info
.\forgeops-console-demo.exe --web-dir .\web --listen 127.0.0.1:9090
```

On Linux:

```bash
chmod u+x forgeops-console forgeops-console-demo
./forgeops-console-demo --build-info
./forgeops-console-demo --web-dir ./web --listen 127.0.0.1:9090
```

Open http://127.0.0.1:9090 and confirm the permanent synthetic banner. Activate
`synthetic-demo`, choose `signalforge`, set scope, and inspect Pods and Services.
Resource changes must clear old objects and selection. Use Tab/Shift+Tab and
Enter/Space to inspect context, namespace, resource, object, and diagnostic
controls; confirm visible focus, selected state, readable errors and scope.
Check 200% zoom and a narrow window. These checks do not certify accessibility;
record the browser/version and any keyboard, screen-reader, or layout failures.
Press Ctrl+C and confirm the terminal prompt returns promptly.

The repository verifier checks archive safety and checksums before execution,
then uses temporary extraction and an unrelated working directory. It exercises
both executable identities, demo queries, explicit-configuration rejection,
production bootstrap with a synthetic canary configuration (no context
activation), Host/Origin/nonce denial, mismatch rejection and whole-pair
restoration. It never contacts Kubernetes. On Windows its process cleanup is
forced; graceful Ctrl+C still requires the operator check above.

## Production use is a separate acceptance step

The production executable requires `--kubeconfig` with one explicit regular
file and `--web-dir` with the paired assets. There is no ambient credential
fallback. Start only with an intentionally selected configuration and an
accepted read-only cluster scope. Never share kubeconfig or tokens in a report.
Exec/auth-provider credentials (including standard EKS AWS exec configurations),
secondary credential files, proxies and insecure TLS are rejected. Listing a
context is not proof that authentication works.

Resources are bounded projections, not raw objects or a complete inventory.
An incomplete warning can reflect primary or supporting pagination and clipped
relationships. Logs and Events can contain application secrets; they are not
guaranteed redacted. Command previews are not executed. There are no writes,
Secrets, shell execution, background collection, export, or ForgeOps intake.
Only the example, resources and diagnostics first-party plugins are compiled
in. They are trusted code, not sandboxed third-party modules.

## Update, rollback and removal

Keep the previous executable/browser pair in its own directory. Stop the old
process before starting a new candidate. Never overlay browser files from a
different build. Verify the new pair with synthetic data first. If acceptance
fails, stop it and restart the previous complete pair. Select scope anew;
sessions are memory-only. The automated same-pair restoration exercise does
not prove rollback to a historical release.

To remove the candidate, stop it and delete only its extracted directory.
Kubeconfig remains outside that directory and is not modified by Console.

## Release hold

A public version/tag/release is held until the C7 gate record establishes the
supported environment and Kubernetes scope, installed operator acceptance,
security/dependency review, accessibility limitations, and rollback evidence.
No candidate workflow can publish a release or change a cluster.
