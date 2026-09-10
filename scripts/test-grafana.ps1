param([ValidateRange(1024,65535)][int]$Port = 3000)
$ErrorActionPreference = 'Stop'
$Base = "http://127.0.0.1:$Port"
$Health = Invoke-RestMethod "$Base/api/health"
if ($Health.database -ne 'ok' -or $Health.version -ne '13.2.1') { throw 'Grafana health/version did not match' }
try {
    Invoke-RestMethod "$Base/api/search" | Out-Null
    throw 'Anonymous dashboard search unexpectedly succeeded'
} catch {
    if (-not $_.Exception.Response -or [int]$_.Exception.Response.StatusCode -ne 401) { throw }
}
$Credential = Get-Credential -Message 'Grafana login for local acceptance queries'
$Password = $Credential.GetNetworkCredential().Password
$Header = @{Authorization='Basic ' + [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($Credential.UserName+':'+$Password))}
$Password=$null
try {
    $Uid = 'signalforge-prometheus'
    $DataSource = Invoke-RestMethod "$Base/api/datasources/uid/$Uid" -Headers $Header
    if ($DataSource.type -ne 'prometheus' -or $DataSource.access -ne 'proxy') { throw 'Unexpected data source' }
    $Dashboards = Invoke-RestMethod "$Base/api/search?tag=signalforge&type=dash-db" -Headers $Header
    if (@($Dashboards).Count -ne 2) { throw 'Expected exactly two SignalForge dashboards' }
    foreach ($DashboardUid in @('signalforge-restaurant-overview','signalforge-scrape-diagnostics')) {
        $D = Invoke-RestMethod "$Base/api/dashboards/uid/$DashboardUid" -Headers $Header
        if (@($D.dashboard.panels).Count -ne 6) { throw "Expected six panels in $DashboardUid" }
        foreach ($Panel in $D.dashboard.panels) {
            foreach ($Target in $Panel.targets) {
                $Encoded = [Uri]::EscapeDataString($Target.expr)
                $Query = Invoke-RestMethod "$Base/api/datasources/proxy/uid/$Uid/api/v1/query?query=$Encoded" -Headers $Header
                if ($Query.status -ne 'success') { throw "Query failed in panel $($Panel.id)" }
                Write-Host "$DashboardUid panel $($Panel.id): query accepted, $(@($Query.data.result).Count) result series"
            }
        }
    }
    $UpQuery = [Uri]::EscapeDataString('sum(up{job="restaurant-api",namespace="forge-restaurant"})')
    $Up = Invoke-RestMethod "$Base/api/datasources/proxy/uid/$Uid/api/v1/query?query=$UpQuery" -Headers $Header
    if (@($Up.data.result).Count -ne 1 -or $Up.data.result[0].value[1] -ne '3') { throw 'Expected three healthy Restaurant API targets' }
} finally { $Header.Clear(); $Credential=$null }
Write-Host 'Authentication, provisioning and query checks passed. Inspect layout, idle/missing states and persisted preferences in the browser before acceptance.'
