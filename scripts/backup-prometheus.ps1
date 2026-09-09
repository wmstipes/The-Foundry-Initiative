param(
    [string]$Namespace = "forge-observability",
    [string]$Deployment = "prometheus",
    [string]$PersistentVolumeClaim = "prometheus-data",
    [string]$ExpectedNode = "forge-head",
    [string]$BackupDirectory = "$env:USERPROFILE\SignalForge-Backups\prometheus",
    [int]$TimeoutSeconds = 180,
    [int]$KeepArchives = 4
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptDir
$ManifestPath = Join-Path $RepoRoot "k8s\prometheus\prometheus-backup-pod.yaml"
$BackupPod = "prometheus-backup"
$Timestamp = (Get-Date).ToUniversalTime().ToString("yyyyMMdd-HHmmssZ")
$ScaledDown = $false
$BackupPodCreated = $false
$BackupValidated = $false
$RecoverySucceeded = $false

if ($KeepArchives -lt 1) {
    throw "KeepArchives must be at least 1"
}

if (-not $env:ComSpec) {
    throw "ComSpec is unavailable; binary-safe Windows command redirection cannot be used"
}

if ($BackupDirectory.Contains('"') -or $BackupDirectory.Contains('%')) {
    throw "BackupDirectory cannot contain double quotes or percent signs"
}

$BackupDirectory = [System.IO.Path]::GetFullPath($BackupDirectory)
[System.IO.Directory]::CreateDirectory($BackupDirectory) | Out-Null
$BackupPath = Join-Path $BackupDirectory "prometheus-tsdb-$Timestamp.tar.gz"
$ChecksumPath = "$BackupPath.sha256"
$BatchPath = Join-Path ([System.IO.Path]::GetTempPath()) "signalforge-prometheus-backup-$Timestamp.cmd"

if (Test-Path $BackupPath) {
    throw "Backup path already exists: $BackupPath"
}

Write-Host "Prometheus cold-backup destination: $BackupPath"
Write-Host "The Deployment will be restored to one replica even if the archive operation fails."

& "$ScriptDir\test-prometheus-backup-ready.ps1" `
    -Namespace $Namespace `
    -TimeoutSeconds 60

$OriginalReplicas = kubectl get deployment $Deployment `
    -n $Namespace `
    -o "jsonpath={.spec.replicas}"

if ($LASTEXITCODE -ne 0 -or $OriginalReplicas -ne "1") {
    throw "Prometheus must have exactly one configured replica before backup"
}

$ClaimPhase = kubectl get pvc $PersistentVolumeClaim `
    -n $Namespace `
    -o "jsonpath={.status.phase}"

if ($LASTEXITCODE -ne 0 -or $ClaimPhase -ne "Bound") {
    throw "PVC $Namespace/$PersistentVolumeClaim must be Bound before backup"
}

try {
    Write-Host "Scaling Prometheus to zero for a consistent cold backup..."
    kubectl scale deployment/$Deployment -n $Namespace --replicas=0 | Out-Null

    if ($LASTEXITCODE -ne 0) {
        throw "Could not scale Prometheus to zero"
    }

    $ScaledDown = $true
    $ShutdownDeadline = (Get-Date).AddSeconds($TimeoutSeconds)
    $RemainingPods = -1

    do {
        $PodListJson = kubectl get pods -n $Namespace -l app=prometheus -o json

        if ($LASTEXITCODE -ne 0 -or -not $PodListJson) {
            throw "Could not check whether Prometheus stopped"
        }

        $RemainingPods = @(
            ($PodListJson | Out-String | ConvertFrom-Json).items
        ).Count

        if ($RemainingPods -eq 0) {
            break
        }

        Start-Sleep -Seconds 2
    } while ((Get-Date) -lt $ShutdownDeadline)

    if ($RemainingPods -ne 0) {
        throw "Prometheus did not stop within $TimeoutSeconds seconds"
    }

    kubectl delete pod $BackupPod -n $Namespace --ignore-not-found --wait=true | Out-Null

    if ($LASTEXITCODE -ne 0) {
        throw "Could not remove a stale Prometheus backup Pod"
    }

    kubectl apply -f $ManifestPath | Out-Null

    if ($LASTEXITCODE -ne 0) {
        throw "Could not create the Prometheus backup Pod"
    }

    $BackupPodCreated = $true
    kubectl wait -n $Namespace --for=condition=Ready "pod/$BackupPod" --timeout="${TimeoutSeconds}s" | Out-Null

    if ($LASTEXITCODE -ne 0) {
        kubectl describe pod $BackupPod -n $Namespace
        throw "Prometheus backup Pod did not become Ready"
    }

    $BackupNode = kubectl get pod $BackupPod -n $Namespace -o "jsonpath={.spec.nodeName}"

    if ($LASTEXITCODE -ne 0 -or $BackupNode -ne $ExpectedNode) {
        throw "Prometheus backup Pod ran on '$BackupNode' instead of $ExpectedNode"
    }

    Write-Host "Streaming the cold TSDB archive directly to the off-node destination..."
    $BatchText = @"
@echo off
kubectl exec -n $Namespace $BackupPod -- /bin/tar -C /prometheus -czf - . > "$BackupPath"
exit /b %errorlevel%
"@
    [System.IO.File]::WriteAllText($BatchPath, $BatchText, [System.Text.Encoding]::ASCII)

    try {
        & $env:ComSpec /d /c $BatchPath
        $ArchiveExitCode = $LASTEXITCODE
    }
    finally {
        Remove-Item $BatchPath -Force -ErrorAction SilentlyContinue
    }

    if ($ArchiveExitCode -ne 0) {
        Remove-Item $BackupPath -Force -ErrorAction SilentlyContinue
        throw "Binary TSDB archive stream failed with exit code $ArchiveExitCode"
    }

    $BackupFile = Get-Item $BackupPath

    if ($BackupFile.Length -le 0) {
        Remove-Item $BackupPath -Force -ErrorAction SilentlyContinue
        throw "The TSDB archive is empty"
    }

    $ArchiveEntries = @(tar -tzf $BackupPath)

    if ($LASTEXITCODE -ne 0) {
        throw "The copied TSDB archive could not be listed"
    }

    $WalEntries = @($ArchiveEntries | Where-Object { $_ -like "./wal/*" })

    if ($WalEntries.Count -eq 0) {
        throw "The copied TSDB archive does not contain a WAL"
    }

    $BlockMetadata = @(
        $ArchiveEntries | Where-Object {
            $_ -match '^\./[0-9A-Z]{26}/meta\.json$'
        }
    )

    $Hash = (Get-FileHash -Algorithm SHA256 $BackupPath).Hash.ToLowerInvariant()
    $ChecksumLine = "$Hash  $([System.IO.Path]::GetFileName($BackupPath))"
    Set-Content -Path $ChecksumPath -Value $ChecksumLine -Encoding ASCII
    $BackupValidated = $true

    Write-Host "Archive bytes: $($BackupFile.Length)"
    Write-Host "SHA-256: $Hash"
    Write-Host "Compacted blocks in archive: $($BlockMetadata.Count)"

    $Archives = @(
        Get-ChildItem -Path $BackupDirectory -Filter "prometheus-tsdb-*.tar.gz" -File |
            Sort-Object Name -Descending
    )

    foreach ($OldArchive in @($Archives | Select-Object -Skip $KeepArchives)) {
        $OldChecksum = "$($OldArchive.FullName).sha256"
        Remove-Item $OldArchive.FullName -Force
        Remove-Item $OldChecksum -Force -ErrorAction SilentlyContinue
        Write-Host "Removed expired backup: $($OldArchive.Name)"
    }

    Write-Host "PASS: cold Prometheus backup copied off forge-head and checksum recorded."

    if ($BlockMetadata.Count -eq 0) {
        Write-Warning "The backup contains only head/WAL data and no compacted block. Wait for Prometheus to create a block before running the promtool restore-analysis gate."
    }
}
finally {
    if (-not $BackupValidated) {
        Remove-Item $BackupPath -Force -ErrorAction SilentlyContinue
        Remove-Item $ChecksumPath -Force -ErrorAction SilentlyContinue
    }

    if ($BackupPodCreated) {
        kubectl delete pod $BackupPod -n $Namespace --ignore-not-found --wait=true | Out-Null
    }

    if ($ScaledDown) {
        Write-Host "Restoring Prometheus to one replica..."
        kubectl scale deployment/$Deployment -n $Namespace --replicas=1 | Out-Null

        if ($LASTEXITCODE -ne 0) {
            Write-Warning "Prometheus could not be scaled back to one replica; manual recovery is required"
        }
        else {
            kubectl rollout status deployment/$Deployment -n $Namespace --timeout="${TimeoutSeconds}s" | Out-Null

            if ($LASTEXITCODE -eq 0) {
                $RecoverySucceeded = $true
            }
            else {
                Write-Warning "Prometheus did not become Ready after the backup; inspect the Deployment immediately"
            }
        }
    }
}

if (-not $RecoverySucceeded) {
    throw "The backup finished, but Prometheus recovery did not complete successfully"
}

& "$ScriptDir\test-prometheus-targets.ps1" `
    -Namespace $Namespace `
    -ExpectedTargetCount 3 `
    -TimeoutSeconds 120

Write-Host "Backup archive: $BackupPath"
Write-Host "Checksum file: $ChecksumPath"
Write-Host "Run '.\scripts\forge.ps1 metrics-restore-test' to validate the newest retained archive."
