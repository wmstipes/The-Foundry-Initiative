# Publish the accepted Console Windows preview

Run after this release-preparation PR is merged and its workflows pass.
The operator approved the narrow Windows prerelease on 2026-09-22.
This procedure publishes the existing archive without rebuilding or renaming it.
It creates a draft, verifies downloaded draft assets, then publishes.
If a command fails, stop and report it; do not force-update tags or overwrite assets.

The assistant could obtain the CI artifact reference but its download URL
returned HTTP 403. The available connector has no release-publication action.
Publication therefore runs through the operator's authenticated GitHub CLI.

From the updated repository root in PowerShell:

```powershell
& {
    $ErrorActionPreference = "Stop"
    $repo = "wmstipes/The-Foundry-Initiative"
    $tag = "forgeops-console-v0.1.0-rc.1"
    $source = "af0f3ec54d842c876e63ccc6cba9c7029756d2f0"
    $name = "forgeops-console-candidate-af0f3ec54d84-windows-amd64.zip"
    $expected = "037841539937826dc3f6094bc3fcbf29529bb4ea17948e69d94ee11246f2d801"
    $archive = Join-Path "$env:USERPROFILE\ForgeOps-C7\run-35768592178" $name
    $notes = (Resolve-Path ".\docs\releases\forgeops-console-v0.1.0-rc.1.md").Path

    if ((Get-FileHash $archive -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expected) {
        throw "Accepted archive hash mismatch."
    }
    gh auth status
    if ($LASTEXITCODE -ne 0) { throw "GitHub CLI authentication failed." }

    $refsJson = gh api "repos/$repo/git/matching-refs/tags/$tag"
    if ($LASTEXITCODE -ne 0) { throw "Unable to check existing tags." }
    $existing = @($refsJson | ConvertFrom-Json | Where-Object { $_.ref -eq "refs/tags/$tag" })
    if ($existing.Count -ne 0) { throw "Tag already exists; stop for inspection." }

    $stage = Join-Path ([IO.Path]::GetTempPath()) ("console-release-" + [guid]::NewGuid())
    New-Item -ItemType Directory -Path $stage | Out-Null
    $sumFile = Join-Path $stage "SHA256SUMS.txt"
    [IO.File]::WriteAllText($sumFile, "$expected  $name" + [Environment]::NewLine, [Text.Encoding]::ASCII)

    gh release create $tag $archive $sumFile --repo $repo --target $source --draft --prerelease --latest=false --title "ForgeOps Console v0.1.0-rc.1 — Windows engineering preview" --notes-file $notes
    if ($LASTEXITCODE -ne 0) { throw "Draft creation/upload failed; inspect before retrying." }

    $download = Join-Path $stage "download"
    gh release download $tag --repo $repo --dir $download
    if ($LASTEXITCODE -ne 0) { throw "Draft asset download failed; draft remains unpublished." }
    $files = @(Get-ChildItem -LiteralPath $download -File)
    if ($files.Count -ne 2 -or !(Test-Path (Join-Path $download $name)) -or !(Test-Path (Join-Path $download "SHA256SUMS.txt"))) {
        throw "Unexpected draft asset set."
    }
    if ((Get-FileHash (Join-Path $download $name) -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expected) {
        throw "Uploaded archive hash mismatch; draft remains unpublished."
    }
    if ((Get-FileHash (Join-Path $download "SHA256SUMS.txt")).Hash -ne (Get-FileHash $sumFile).Hash) {
        throw "Uploaded checksum file differs; draft remains unpublished."
    }
    $metadataJson = gh release view $tag --repo $repo --json isDraft,isPrerelease,targetCommitish,tagName
    if ($LASTEXITCODE -ne 0) { throw "Cannot verify draft metadata." }
    $metadata = $metadataJson | ConvertFrom-Json
    if (!$metadata.isDraft -or !$metadata.isPrerelease -or $metadata.targetCommitish -ne $source -or $metadata.tagName -ne $tag) {
        throw "Unexpected draft identity or publication state."
    }

    gh release edit $tag --repo $repo --target $source --draft=false --prerelease --latest=false
    if ($LASTEXITCODE -ne 0) { throw "Publication failed; inspect the release state." }
    $refJson = gh api "repos/$repo/git/ref/tags/$tag"
    if ($LASTEXITCODE -ne 0) { throw "Cannot verify published tag." }
    $ref = $refJson | ConvertFrom-Json
    if ($ref.object.type -ne "commit" -or $ref.object.sha -ne $source) {
        throw "Published tag differs from expected source; stop for inspection."
    }
    gh release view $tag --repo $repo --json url,isDraft,isPrerelease,tagName,targetCommitish,assets
    if ($LASTEXITCODE -ne 0) { throw "Cannot read published release state." }
}
```

The only uploaded assets are the accepted Windows ZIP and its checksum file.
The prerelease is explicitly not marked Latest, preserving the separate
ForgeOps stable-release designation. No Linux binary is published here.
Keep the final JSON output as publication evidence; a merged documentation PR
alone does not prove publication.

Commands follow [GitHub CLI create](https://cli.github.com/manual/gh_release_create)
and [edit](https://cli.github.com/manual/gh_release_edit) semantics.
