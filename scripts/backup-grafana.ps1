param(
    [Parameter(Mandatory)][string]$ExpectedContext,
    [Parameter(Mandatory)][string]$BackupDirectory,
    [Parameter(Mandatory)][switch]$EncryptedDestinationVerified,
    [switch]$PreUpgrade
)
. (Join-Path $PSScriptRoot 'grafana-common.ps1')
if (-not $EncryptedDestinationVerified) { throw 'Verify encrypted destination storage before backup' }
Assert-GrafanaContext -ExpectedContext $ExpectedContext
$BackupDirectory = [IO.Path]::GetFullPath($BackupDirectory)
$Repository = [IO.Path]::GetFullPath((Split-Path $PSScriptRoot -Parent)).TrimEnd('\') + '\'
if ($BackupDirectory.TrimEnd('\') -eq $Repository.TrimEnd('\') -or $BackupDirectory.StartsWith($Repository,[StringComparison]::OrdinalIgnoreCase)) { throw 'Backups must be outside the repository' }
if (-not (Test-Path -LiteralPath $BackupDirectory -PathType Container)) { throw 'Create and protect the backup directory first' }
$Deployment = Invoke-GrafanaKubectl -Arguments @('get','deployment','grafana','-n',$GrafanaNamespace,'-o','json') | ConvertFrom-Json
if ($Deployment.spec.replicas -ne 1) { throw 'Expected one Grafana replica before backup' }
$Image = $Deployment.spec.template.spec.containers[0].image
$Name = 'grafana-backup'
$Stamp = [DateTime]::UtcNow.ToString('yyyyMMdd-HHmmssZ')
$Prefix = if ($PreUpgrade) { 'grafana-pre-upgrade' } else { 'grafana-weekly' }
$Archive = Join-Path $BackupDirectory "$Prefix-$Stamp.tar.gz"
$TemporaryArchive = "$Archive.partial"
$Pod = @{
    apiVersion='v1';kind='Pod';metadata=@{name=$Name;namespace=$GrafanaNamespace;labels=@{app=$Name;project='signalforge'}}
    spec=@{restartPolicy='Never';serviceAccountName='grafana';automountServiceAccountToken=$false
        securityContext=@{runAsNonRoot=$true;runAsUser=472;runAsGroup=0;fsGroup=0;seccompProfile=@{type='RuntimeDefault'}}
        tolerations=@(@{key='node-role.kubernetes.io/control-plane';operator='Exists';effect='NoSchedule'})
        containers=@(@{name='backup';image=$Image;command=@('/bin/sh','-ec');args=@('tar -czf /backup/grafana.tar.gz -C /var/lib/grafana .; sha256sum /backup/grafana.tar.gz > /backup/checksum; touch /backup/ready; sleep 3600')
            resources=@{requests=@{cpu='50m';memory='128Mi'};limits=@{cpu='500m';memory='512Mi'}}
            securityContext=@{allowPrivilegeEscalation=$false;readOnlyRootFilesystem=$true;capabilities=@{drop=@('ALL')}}
            readinessProbe=@{exec=@{command=@('/bin/sh','-ec','test -f /backup/ready')};periodSeconds=5}
            volumeMounts=@(@{name='data';mountPath='/var/lib/grafana';readOnly=$true},@{name='archive';mountPath='/backup'})})
        volumes=@(@{name='data';persistentVolumeClaim=@{claimName='grafana-data';readOnly=$true}},@{name='archive';emptyDir=@{sizeLimit='3Gi'}})
    }
}
$Started = $false
try {
    Invoke-GrafanaKubectl -Arguments @('delete','pod',$Name,'-n',$GrafanaNamespace,'--ignore-not-found','--wait=true','--timeout=60s')
    $Started = $true
    Invoke-GrafanaKubectl -Arguments @('scale','deployment/grafana','-n',$GrafanaNamespace,'--replicas=0')
    Invoke-GrafanaKubectl -Arguments @('wait','pod','-n',$GrafanaNamespace,'-l','app=grafana','--for=delete','--timeout=180s')
    $Pod | ConvertTo-Json -Depth 20 | & kubectl create -f -
    if ($LASTEXITCODE -ne 0) { throw 'Backup helper creation failed' }
    Invoke-GrafanaKubectl -Arguments @('wait',"pod/$Name",'-n',$GrafanaNamespace,'--for=condition=Ready','--timeout=300s')
    $ExpectedHash = ((Invoke-GrafanaKubectl -Arguments @('exec',$Name,'-n',$GrafanaNamespace,'--','cat','/backup/checksum') | Out-String).Trim() -split '\s+')[0]
    # Local destination is relative to avoid kubectl cp interpreting a Windows drive colon as a remote Pod.
    Push-Location $BackupDirectory
    try { Invoke-GrafanaKubectl -Arguments @('cp',"${GrafanaNamespace}/${Name}:/backup/grafana.tar.gz",("./" + [IO.Path]::GetFileName($TemporaryArchive))) }
    finally { Pop-Location }
    $ActualHash = (Get-FileHash -LiteralPath $TemporaryArchive -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($ActualHash -ne $ExpectedHash) { throw 'Copied archive checksum mismatch; retained as .partial' }
    Move-Item -LiteralPath $TemporaryArchive -Destination $Archive
    $Commit = (& git -C (Split-Path $PSScriptRoot -Parent) rev-parse HEAD | Out-String).Trim()
    [ordered]@{timestampUtc=$Stamp;sha256=$ActualHash;bytes=(Get-Item -LiteralPath $Archive).Length;image=$Image;gitCommit=$Commit;type=$Prefix;restoreVerified=$false} |
        ConvertTo-Json | Set-Content -LiteralPath "$Archive.json" -Encoding UTF8
    Write-Host "Verified off-node archive: $Archive"
} finally {
    if ($Started) {
        try { Invoke-GrafanaKubectl -Arguments @('delete','pod',$Name,'-n',$GrafanaNamespace,'--ignore-not-found','--wait=true','--timeout=120s') }
        finally {
            Invoke-GrafanaKubectl -Arguments @('scale','deployment/grafana','-n',$GrafanaNamespace,'--replicas=1')
            Invoke-GrafanaKubectl -Arguments @('rollout','status','deployment/grafana','-n',$GrafanaNamespace,'--timeout=300s')
        }
    }
}
Write-Host 'Verify login and dashboards. Keep four successful weekly archives; prune manually only after acceptance. No backups were deleted.'
