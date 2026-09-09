param(
    [string]$Namespace = "forge-observability",
    [string]$Service = "prometheus",
    [int]$TimeoutSeconds = 60
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Timestamp = Get-Date -Format "yyyyMMddHHmmssfff"
$PodName = "prometheus-block-check-$Timestamp"
$Query = "prometheus_tsdb_blocks_loaded"
$EncodedQuery = [uri]::EscapeDataString($Query)
$Url = "http://$Service.$Namespace.svc.cluster.local:9090/api/v1/query?query=$EncodedQuery"
$PodLifetimeSeconds = [Math]::Max(60, $TimeoutSeconds + 60)

Write-Host "Checking whether Prometheus has a compacted TSDB block..."

try {
    kubectl run $PodName `
        -n $Namespace `
        --image=curlimages/curl:8.22.0 `
        --restart=Never `
        --command -- sleep $PodLifetimeSeconds | Out-Null

    if ($LASTEXITCODE -ne 0) {
        throw "Could not create Prometheus block-check Pod $PodName"
    }

    kubectl wait `
        -n $Namespace `
        --for=condition=Ready `
        "pod/$PodName" `
        --timeout=60s | Out-Null

    if ($LASTEXITCODE -ne 0) {
        throw "Prometheus block-check Pod $PodName did not become Ready"
    }

    $Deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    $BlocksLoaded = $null

    do {
        $Output = kubectl exec -n $Namespace $PodName -- curl -fsS $Url 2>$null

        if ($LASTEXITCODE -eq 0 -and $Output) {
            try {
                $Response = $Output | ConvertFrom-Json
                $Results = @($Response.data.result)

                if ($Results.Count -eq 1) {
                    $BlocksLoaded = [int]$Results[0].value[1]
                    break
                }
            }
            catch {
                $BlocksLoaded = $null
            }
        }

        Start-Sleep -Seconds 3
    } while ((Get-Date) -lt $Deadline)

    if ($null -eq $BlocksLoaded) {
        throw "Could not read prometheus_tsdb_blocks_loaded within $TimeoutSeconds seconds"
    }

    Write-Host "Compacted TSDB blocks loaded: $BlocksLoaded"

    if ($BlocksLoaded -lt 1) {
        throw "Prometheus has not created its first compacted block; wait and run metrics-backup-ready again"
    }

    Write-Host "PASS: Prometheus is ready for an acceptance backup and promtool restore analysis."
}
finally {
    kubectl delete pod $PodName -n $Namespace --ignore-not-found | Out-Null
}
