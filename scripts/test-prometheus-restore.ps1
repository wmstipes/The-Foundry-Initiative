param(
    [string]$Namespace = "forge-observability",
    [string]$BackupDirectory = "$env:USERPROFILE\SignalForge-Backups\prometheus",
    [string]$BackupPath = "",
    [string]$SshHost = "forge-head",
    [string]$ExpectedNode = "forge-head",
    [int]$TimeoutSeconds = 180
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptDir
$ManifestPath = Join-Path $RepoRoot "k8s\prometheus\prometheus-restore-validation-pod.yaml"
$ValidationPod = "prometheus-restore-validation"
$RestoreDirectory = "/mnt/signalforge-prometheus/restore-validation"
$ExpectedFilesystemUuid = "4f2feee5-72a7-4f32-a351-b4253c4a0854"
$RestoreDirectoryCreated = $false
$ValidationPodCreated = $false
$ValidationSucceeded = $false
$CleanupSucceeded = $true
$Timestamp = (Get-Date).ToUniversalTime().ToString("yyyyMMdd-HHmmssZ")
$BatchPath = Join-Path ([System.IO.Path]::GetTempPath()) "signalforge-prometheus-restore-$Timestamp.cmd"

if ($SshHost -notmatch '^[A-Za-z0-9._-]+$') {
    throw "SshHost contains unsupported characters"
}

if (-not $env:ComSpec) {
    throw "ComSpec is unavailable; binary-safe Windows command redirection cannot be used"
}

if (-not $BackupPath) {
    $NewestBackup = Get-ChildItem `
        -Path $BackupDirectory `
        -Filter "prometheus-tsdb-*.tar.gz" `
        -File `
        -ErrorAction Stop |
        Sort-Object Name -Descending |
        Select-Object -First 1

    if ($null -eq $NewestBackup) {
        throw "No Prometheus backup archive exists in $BackupDirectory"
    }

    $BackupPath = $NewestBackup.FullName
}

$BackupPath = [System.IO.Path]::GetFullPath($BackupPath)
$ChecksumPath = "$BackupPath.sha256"

if (-not (Test-Path $BackupPath -PathType Leaf)) {
    throw "Backup archive does not exist: $BackupPath"
}

if (-not (Test-Path $ChecksumPath -PathType Leaf)) {
    throw "Checksum file does not exist: $ChecksumPath"
}

if ($BackupPath.Contains('"') -or $BackupPath.Contains('%')) {
    throw "BackupPath cannot contain double quotes or percent signs"
}

$ExpectedHash = ((Get-Content $ChecksumPath -Raw).Trim() -split '\s+')[0].ToLowerInvariant()
$ActualHash = (Get-FileHash -Algorithm SHA256 $BackupPath).Hash.ToLowerInvariant()

if ($ExpectedHash -notmatch '^[0-9a-f]{64}$' -or $ActualHash -ne $ExpectedHash) {
    throw "Backup SHA-256 verification failed"
}

$ArchiveEntries = @(tar -tzf $BackupPath)

if ($LASTEXITCODE -ne 0) {
    throw "Backup archive could not be listed"
}

$BlockMetadata = @(
    $ArchiveEntries | Where-Object {
        $_ -match '^\./[0-9A-Z]{26}/meta\.json$'
    }
)

if ($BlockMetadata.Count -eq 0) {
    throw "The backup contains no compacted TSDB block. Create a newer backup after at least two hours of collection, then rerun this validation."
}

Write-Host "Validated local archive checksum: $ActualHash"
Write-Host "Compacted blocks available for promtool analysis: $($BlockMetadata.Count)"
Write-Host "The restored copy will use $RestoreDirectory; active data remains in the separate data directory."

$ExistingRestorePathCheck = & ssh $SshHost "test ! -e $RestoreDirectory"

if ($LASTEXITCODE -ne 0) {
    throw "$RestoreDirectory already exists or could not be checked. Inspect it manually; this script will not overwrite it."
}

try {
    Write-Host "Creating the isolated restore-validation directory on the NVMe..."
    & ssh -t $SshHost "sudo install -d -o 65534 -g 65534 -m 0750 $RestoreDirectory"

    if ($LASTEXITCODE -ne 0) {
        throw "Could not create $RestoreDirectory on $SshHost"
    }

    $RestoreDirectoryCreated = $true
    $CleanupSucceeded = $false
    $RemoteMount = & ssh $SshHost "findmnt -n -o UUID,FSTYPE,TARGET -T $RestoreDirectory"

    if (
        $LASTEXITCODE -ne 0 -or
        $RemoteMount -notmatch $ExpectedFilesystemUuid -or
        $RemoteMount -notmatch 'ext4' -or
        $RemoteMount -notmatch '/mnt/signalforge-prometheus'
    ) {
        throw "Restore-validation directory is not on the expected NVMe filesystem"
    }

    kubectl delete pod $ValidationPod -n $Namespace --ignore-not-found --wait=true | Out-Null

    if ($LASTEXITCODE -ne 0) {
        throw "Could not remove a stale restore-validation Pod"
    }

    kubectl apply -f $ManifestPath | Out-Null

    if ($LASTEXITCODE -ne 0) {
        throw "Could not create the restore-validation Pod"
    }

    $ValidationPodCreated = $true
    kubectl wait -n $Namespace --for=condition=Ready "pod/$ValidationPod" --timeout="${TimeoutSeconds}s" | Out-Null

    if ($LASTEXITCODE -ne 0) {
        kubectl describe pod $ValidationPod -n $Namespace
        throw "Restore-validation Pod did not become Ready"
    }

    $ValidationNode = kubectl get pod $ValidationPod -n $Namespace -o "jsonpath={.spec.nodeName}"

    if ($LASTEXITCODE -ne 0 -or $ValidationNode -ne $ExpectedNode) {
        throw "Restore-validation Pod ran on '$ValidationNode' instead of $ExpectedNode"
    }

    Write-Host "Extracting the off-node archive into the isolated validation directory..."
    $BatchText = @"
@echo off
kubectl exec -i -n $Namespace $ValidationPod -- /bin/tar -C /validation -xzf - < "$BackupPath"
exit /b %errorlevel%
"@
    [System.IO.File]::WriteAllText($BatchPath, $BatchText, [System.Text.Encoding]::ASCII)

    try {
        & $env:ComSpec /d /c $BatchPath
        $ExtractExitCode = $LASTEXITCODE
    }
    finally {
        Remove-Item $BatchPath -Force -ErrorAction SilentlyContinue
    }

    if ($ExtractExitCode -ne 0) {
        throw "Backup extraction failed with exit code $ExtractExitCode"
    }

    kubectl exec -n $Namespace $ValidationPod -- /bin/sh -c 'test -d /validation/wal && test -n "$(ls -A /validation/wal)"'

    if ($LASTEXITCODE -ne 0) {
        throw "Restored TSDB does not contain a readable WAL"
    }

    kubectl exec -n $Namespace $ValidationPod -- /bin/sh -c 'set -- /validation/*/meta.json; test -f "$1"'

    if ($LASTEXITCODE -ne 0) {
        throw "Restored TSDB does not contain readable block metadata"
    }

    Write-Host "Restored TSDB blocks:"
    kubectl exec -n $Namespace $ValidationPod -- /bin/promtool tsdb list /validation

    if ($LASTEXITCODE -ne 0) {
        throw "promtool could not list the restored TSDB blocks"
    }

    Write-Host "Analyzing the newest restored TSDB block:"
    kubectl exec -n $Namespace $ValidationPod -- /bin/promtool tsdb analyze /validation

    if ($LASTEXITCODE -ne 0) {
        throw "promtool could not analyze the restored TSDB"
    }

    $ValidationSucceeded = $true
}
finally {
    Remove-Item $BatchPath -Force -ErrorAction SilentlyContinue

    if ($ValidationPodCreated) {
        kubectl delete pod $ValidationPod -n $Namespace --ignore-not-found --wait=true | Out-Null
    }

    if ($RestoreDirectoryCreated) {
        Write-Host "Removing only the isolated restore-validation copy; the off-node archive and active TSDB are retained."

        if ($RestoreDirectory -ne "/mnt/signalforge-prometheus/restore-validation") {
            throw "Refusing cleanup because the restore directory is not the exact approved path"
        }

        & ssh -t $SshHost "sudo rm -rf -- /mnt/signalforge-prometheus/restore-validation"

        if ($LASTEXITCODE -ne 0) {
            Write-Warning "Could not remove the isolated restore-validation directory; inspect it manually"
        }
        else {
            & ssh $SshHost "test ! -e /mnt/signalforge-prometheus/restore-validation"

            if ($LASTEXITCODE -eq 0) {
                $CleanupSucceeded = $true
            }
            else {
                Write-Warning "The isolated restore-validation directory still exists; inspect it manually"
            }
        }
    }
}

if (-not $CleanupSucceeded) {
    throw "Restore validation finished, but isolated-copy cleanup did not succeed"
}

if ($ValidationSucceeded) {
    Write-Host "PASS: off-node backup checksum, extraction, TSDB structure, promtool analysis, and isolated-copy cleanup succeeded."
}
