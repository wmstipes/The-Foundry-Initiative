param(
    [Parameter(Mandatory)][string]$ExpectedContext,
    [Parameter(Mandatory)][string]$ExpectedFilesystemUuid,
    [string]$SshTarget = 'wmstipes@192.168.243.110'
)
. (Join-Path $PSScriptRoot 'grafana-common.ps1')
Assert-GrafanaContext -ExpectedContext $ExpectedContext
Assert-GrafanaMount -ExpectedFilesystemUuid $ExpectedFilesystemUuid -SshTarget $SshTarget

# Bootstrap Secret is managed outside Git. Verify required keys without printing values.
$Secret = Invoke-GrafanaKubectl -Arguments @('get','secret','grafana-admin','-n',$GrafanaNamespace,'-o','json') | ConvertFrom-Json
foreach ($Key in @('admin-user','admin-password','secret-key')) {
    if (-not $Secret.data.PSObject.Properties[$Key] -or -not $Secret.data.$Key) { throw "Missing Secret key: $Key" }
}
$Secret = $null
$StorageClass = Invoke-GrafanaKubectl -Arguments @('get','storageclass','signalforge-local-nvme','-o','json') | ConvertFrom-Json
if ($StorageClass.provisioner -ne 'kubernetes.io/no-provisioner' -or $StorageClass.volumeBindingMode -ne 'WaitForFirstConsumer') {
    throw 'Unexpected shared StorageClass; refusing to modify it'
}
# Validate and display the concrete resource diff before modifying live resources.
# The preflight Pod is created only after its ServiceAccount exists.
foreach ($File in @('grafana-service-account.yaml','grafana-local-pv.yaml','grafana-data-pvc.yaml','grafana-service.yaml','grafana-deployment.yaml')) {
    $Path = Join-Path $GrafanaManifestPath $File
    Invoke-GrafanaKubectl -Arguments @('apply','--dry-run=server','-f',$Path)
    & kubectl diff -f $Path
    if ($LASTEXITCODE -gt 1) { throw "Resource diff failed: $File" }
}
foreach ($File in @('grafana-service-account.yaml','grafana-local-pv.yaml','grafana-data-pvc.yaml')) {
    Invoke-GrafanaKubectl -Arguments @('apply','-f',(Join-Path $GrafanaManifestPath $File))
}
$Running = Invoke-GrafanaKubectl -Arguments @('get','pods','-n',$GrafanaNamespace,'-l','app=grafana','-o','json') | ConvertFrom-Json
if (@($Running.items).Count -eq 0) {
    try {
        Invoke-GrafanaKubectl -Arguments @('delete','pod','grafana-storage-preflight','-n',$GrafanaNamespace,'--ignore-not-found','--wait=true','--timeout=60s')
        Invoke-GrafanaKubectl -Arguments @('apply','-f',(Join-Path $GrafanaManifestPath 'grafana-storage-preflight-pod.yaml'))
        Invoke-GrafanaKubectl -Arguments @('wait','pod/grafana-storage-preflight','-n',$GrafanaNamespace,'--for=jsonpath={.status.phase}=Succeeded','--timeout=300s')
        Invoke-GrafanaKubectl -Arguments @('logs','grafana-storage-preflight','-n',$GrafanaNamespace)
    } finally {
        Invoke-GrafanaKubectl -Arguments @('delete','pod','grafana-storage-preflight','-n',$GrafanaNamespace,'--ignore-not-found','--wait=true','--timeout=60s')
    }
}
$Claim = Invoke-GrafanaKubectl -Arguments @('get','pvc','grafana-data','-n',$GrafanaNamespace,'-o','json') | ConvertFrom-Json
if ($Claim.status.phase -ne 'Bound' -or $Claim.spec.volumeName -ne 'grafana-local-nvme') { throw 'Grafana PVC is not bound to its expected PV' }

$Maps = @(
    @{Name='grafana-config';Directory='config'},
    @{Name='grafana-datasources';Directory='provisioning/datasources'},
    @{Name='grafana-providers';Directory='provisioning/dashboards'},
    @{Name='grafana-dashboards';Directory='dashboards'}
)
foreach ($Map in $Maps) {
    $Rendered = Invoke-GrafanaKubectl -Arguments @('create','configmap',$Map.Name,'-n',$GrafanaNamespace,"--from-file=$(Join-Path $GrafanaManifestPath $Map.Directory)",'--dry-run=client','-o','json')
    $Rendered | & kubectl apply -f -
    if ($LASTEXITCODE -ne 0) { throw "ConfigMap apply failed: $($Map.Name)" }
}
Invoke-GrafanaKubectl -Arguments @('apply','-f',(Join-Path $GrafanaManifestPath 'grafana-service.yaml'))
Invoke-GrafanaKubectl -Arguments @('apply','-f',(Join-Path $GrafanaManifestPath 'grafana-deployment.yaml'))
# Existing Pods need a restart for settings/data-source changes (dashboard files poll).
if (@($Running.items).Count -gt 0) {
    Invoke-GrafanaKubectl -Arguments @('rollout','restart','deployment/grafana','-n',$GrafanaNamespace)
}
Invoke-GrafanaKubectl -Arguments @('rollout','status','deployment/grafana','-n',$GrafanaNamespace,'--timeout=300s')
Invoke-GrafanaKubectl -Arguments @('get','pods,service,pvc','-n',$GrafanaNamespace,'-l','app=grafana','-o','wide')
Write-Host 'Deployment is Ready; dashboard, persistence and recovery acceptance are still required.'
