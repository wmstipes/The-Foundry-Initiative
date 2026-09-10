param(
    [Parameter(Mandatory)][string]$ExpectedContext,
    [Parameter(Mandatory)][string]$Archive,
    [string]$RecoverySecretName = 'grafana-admin'
)
. (Join-Path $PSScriptRoot 'grafana-common.ps1')
Assert-GrafanaContext -ExpectedContext $ExpectedContext
$Archive = (Resolve-Path -LiteralPath $Archive).Path
$Evidence = Get-Content -LiteralPath "$Archive.json" -Raw | ConvertFrom-Json
if ((Get-FileHash -LiteralPath $Archive -Algorithm SHA256).Hash.ToLowerInvariant() -ne $Evidence.sha256) { throw 'Backup checksum mismatch' }
if ($Evidence.image -notmatch '^grafana/grafana:[0-9.]+@sha256:[a-f0-9]{64}$') { throw 'Backup image is not a pinned official Grafana image' }
$Name = 'grafana-restore-validation'
$Existing = Invoke-GrafanaKubectl -Arguments @('get','pod',$Name,'-n',$GrafanaNamespace,'--ignore-not-found','-o','name')
if ($Existing) { throw 'Restore-validation Pod already exists; inspect it before deliberate cleanup' }
$Source = Invoke-GrafanaKubectl -Arguments @('get','deployment','grafana','-n',$GrafanaNamespace,'-o','json') | ConvertFrom-Json
$Spec = $Source.spec.template.spec
$Spec | Add-Member -NotePropertyName restartPolicy -NotePropertyValue 'Never' -Force
$Container = $Spec.containers[0]
$Container.image = $Evidence.image
foreach ($Env in $Container.env) {
    if ($Env.PSObject.Properties['valueFrom']) { $Env.valueFrom.secretKeyRef.name = $RecoverySecretName }
}
$Container | Add-Member -NotePropertyName command -NotePropertyValue @('/bin/sh','-ec') -Force
$Container | Add-Member -NotePropertyName args -NotePropertyValue @('while [ ! -f /restore/start ]; do sleep 1; done; tar -xzf /restore/grafana.tar.gz -C /var/lib/grafana; exec /run.sh') -Force
# Allow time for an operator-side copy before normal health checks begin.
$Container.startupProbe.failureThreshold = 180
$Spec.volumes = @($Spec.volumes | Where-Object { $_.name -ne 'data' }) + @(
    @{name='data';emptyDir=@{sizeLimit='4Gi'}},@{name='restore';emptyDir=@{sizeLimit='3Gi'}})
$Container.volumeMounts = @($Container.volumeMounts) + @(@{name='restore';mountPath='/restore'})
$Pod = @{apiVersion='v1';kind='Pod';metadata=@{name=$Name;namespace=$GrafanaNamespace;labels=@{app=$Name;project='signalforge'}};spec=$Spec}
$Started = [DateTime]::UtcNow
$Pod | ConvertTo-Json -Depth 40 | & kubectl create -f -
if ($LASTEXITCODE -ne 0) { throw 'Restore Pod creation failed' }
try {
    Invoke-GrafanaKubectl -Arguments @('wait',"pod/$Name",'-n',$GrafanaNamespace,'--for=jsonpath={.status.phase}=Running','--timeout=180s')
    Push-Location (Split-Path $Archive -Parent)
    try { Invoke-GrafanaKubectl -Arguments @('cp',("./"+[IO.Path]::GetFileName($Archive)),"${GrafanaNamespace}/${Name}:/restore/grafana.tar.gz") }
    finally { Pop-Location }
    $RemoteHash = ((Invoke-GrafanaKubectl -Arguments @('exec',$Name,'-n',$GrafanaNamespace,'--','sha256sum','/restore/grafana.tar.gz') | Out-String).Trim() -split '\s+')[0]
    if ($RemoteHash -ne $Evidence.sha256) { throw 'Restore Pod copy checksum mismatch' }
    Invoke-GrafanaKubectl -Arguments @('exec',$Name,'-n',$GrafanaNamespace,'--','touch','/restore/start')
    Invoke-GrafanaKubectl -Arguments @('wait',"pod/$Name",'-n',$GrafanaNamespace,'--for=condition=Ready','--timeout=300s')
} catch {
    Write-Warning 'Isolated Pod retained for inspection. Production data was not mounted. Delete only grafana-restore-validation after inspection.'
    throw
}
Write-Host "Restore started UTC: $($Started.ToString('o')); Ready after $([Math]::Round(([DateTime]::UtcNow-$Started).TotalSeconds)) seconds."
Write-Host 'Readiness is not full recovery acceptance. Use the matching backup-era encryption key and configuration.'
Write-Host 'Forward: kubectl -n forge-observability port-forward --address 127.0.0.1 pod/grafana-restore-validation 3001:3000'
Write-Host 'Then run test-grafana.ps1 -Port 3001 and verify login/preferences. Record total elapsed time through usable dashboards.'
Write-Host 'Cleanup: kubectl -n forge-observability delete pod grafana-restore-validation --wait=true'
