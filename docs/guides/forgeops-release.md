# ForgeOps v1 release and installation guide

ForgeOps v1 is distributed only through the repository's GitHub Release for
tag `forgeops-v1.0.0`. The supported release assets are:

- `signalforge_forgeops-1.0.0-py3-none-any.whl`; and
- `SHA256SUMS.txt`.

There is no PyPI package, container image, cluster deployment, background
service, or external service. A Milestone 064 CI artifact is a review candidate,
not a public release. Milestone 065 alone may create the tag and GitHub Release.

## Requirements

- Windows PowerShell;
- an isolated Python 3.11, 3.12, 3.13, or 3.14 environment; and
- both files downloaded from the same reviewed GitHub Release or approved CI
  candidate.

The wheel has no third-party runtime dependencies.

## Verify the downloaded wheel

Run these commands from the directory containing both downloaded files:

~~~powershell
$wheel = ".\signalforge_forgeops-1.0.0-py3-none-any.whl"
$expectedLine = (Get-Content -LiteralPath .\SHA256SUMS.txt -Raw).Trim()
$expectedDigest, $expectedName = $expectedLine -split "\s+", 2

if ($expectedName -ne (Split-Path -Leaf $wheel)) {
  throw "The checksum record names an unexpected file."
}

$actualDigest = (Get-FileHash -LiteralPath $wheel -Algorithm SHA256).Hash.ToLowerInvariant()
if ($actualDigest -ne $expectedDigest.ToLowerInvariant()) {
  throw "The wheel SHA-256 digest does not match SHA256SUMS.txt."
}
~~~

A match proves that the two downloaded files agree. Because the checksum file
is unsigned, it does not independently prove authorship or establish chain of
custody. Obtain both assets from the reviewed release and verify the release tag
and source commit separately when that assurance is required.

## Install into a fresh isolated environment

Do not upgrade an unknown or editable pre-v1 environment in place. Preserve it
for rollback, create a fresh environment, and install only the verified wheel:

~~~powershell
if (Test-Path -LiteralPath .\.venv) {
  if (Test-Path -LiteralPath .\.venv-pre-forgeops-v1) {
    throw ".venv-pre-forgeops-v1 already exists. Resolve it before continuing."
  }
  Rename-Item -LiteralPath .\.venv -NewName .venv-pre-forgeops-v1
}

py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --no-index `
  .\signalforge_forgeops-1.0.0-py3-none-any.whl
.\.venv\Scripts\forgeops.exe provenance
~~~

Substitute another supported Python minor version when deliberate. Provenance
must report status `OK`, distribution `signalforge-forgeops`, distribution and
module version `1.0.0`, execution mode `local-install`, and the intended isolated
Python executable.

## Run the offline acceptance path

From the repository root, use the installed command against reviewed local
fixtures. These checks do not use a kubeconfig, kubectl, HTTP endpoint, package
registry, or live system:

~~~powershell
.\.venv\Scripts\forgeops.exe --help
.\.venv\Scripts\python.exe -m forgeops --help
.\.venv\Scripts\forgeops.exe evidence validate `
  --input .\tests\fixtures\forgeops\evaluated-json-golden.json
.\.venv\Scripts\forgeops.exe scenario replay `
  --before .\tests\fixtures\forgeops\scenarios\stable-baseline\before.json `
  --after .\tests\fixtures\forgeops\scenarios\stable-baseline\after.json `
  --expected .\tests\fixtures\forgeops\scenarios\stable-baseline\expected-comparison.json
~~~

Validation success establishes only that the supplied artifact satisfies its
contract. Replay `MATCH` establishes only an exact deterministic match for the
supplied scenario.

## Roll back or remove

To roll back before the new environment is accepted, remove only the newly
created `.venv` and restore the preserved directory:

~~~powershell
if (Test-Path -LiteralPath .\.venv) {
  Remove-Item -LiteralPath .\.venv -Recurse -Force
}
if (Test-Path -LiteralPath .\.venv-pre-forgeops-v1) {
  Rename-Item -LiteralPath .\.venv-pre-forgeops-v1 -NewName .venv
}
~~~

After acceptance, the operator may deliberately remove the preserved pre-v1
environment. Removing a virtual environment does not remove evidence artifacts
stored elsewhere.

## Release automation boundary

The tag workflow tests the tagged source on Python 3.11-3.14, builds the wheel
twice, requires byte-identical results, validates the exact wheel and checksum,
installs that wheel without a registry on every supported Python version, and
only then creates the GitHub Release. Repository content is read-only in all
jobs except the final publication job, whose sole write authority is attaching
the reviewed wheel and checksum to the exact product tag.

The workflow cannot deploy, access a cluster, contact an application endpoint,
publish to PyPI, build or publish a container, or authorize remediation.
