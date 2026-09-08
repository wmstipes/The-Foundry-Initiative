param(
    [string]$Namespace = "forge-observability",
    [string]$Service = "prometheus",
    [int]$ExpectedTargetCount = 3,
    [int]$TimeoutSeconds = 120
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Timestamp = Get-Date -Format "yyyyMMddHHmmssfff"
$PodName = "prometheus-query-$Timestamp"
$Query = "count(up{job=`"restaurant-api`"} == 1)"
$EncodedQuery = [uri]::EscapeDataString($Query)
$Url = "http://$Service.$Namespace.svc.cluster.local:9090/api/v1/query?query=$EncodedQuery"
$PodLifetimeSeconds = [Math]::Max(60, $TimeoutSeconds + 60)

Write-Host "Waiting for $ExpectedTargetCount healthy Restaurant API Prometheus targets..."

try {
    kubectl run $PodName `
        -n $Namespace `
        --image=curlimages/curl:8.22.0 `
        --restart=Never `
        --command -- sleep $PodLifetimeSeconds | Out-Null

    if ($LASTEXITCODE -ne 0) {
        throw "Could not create Prometheus query Pod $PodName"
    }

    kubectl wait `
        -n $Namespace `
        --for=condition=Ready `
        "pod/$PodName" `
        --timeout=60s | Out-Null

    if ($LASTEXITCODE -ne 0) {
        throw "Prometheus query Pod $PodName did not become ready"
    }

    $Deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    $TargetCount = $null
    $LastQueryError = $null

    do {
        $Output = kubectl exec `
            -n $Namespace `
            $PodName `
            -- curl -fsS $Url 2>$null

        if ($LASTEXITCODE -eq 0 -and $Output) {
            try {
                $Response = $Output | ConvertFrom-Json
                $Results = @($Response.data.result)

                if ($Results.Count -eq 1) {
                    $TargetCount = [int]$Results[0].value[1]

                    if ($TargetCount -eq $ExpectedTargetCount) {
                        Write-Host "Healthy Restaurant API targets: $TargetCount"
                        return
                    }
                }
            }
            catch {
                $LastQueryError = $_.Exception.Message
            }
        }

        Start-Sleep -Seconds 5
    } while ((Get-Date) -lt $Deadline)

    if ($null -ne $TargetCount) {
        throw "Expected $ExpectedTargetCount healthy Restaurant API targets, but Prometheus reported $TargetCount"
    }

    if ($LastQueryError) {
        throw "Prometheus returned an unreadable query response: $LastQueryError"
    }

    throw "Could not query Prometheus within $TimeoutSeconds seconds"
}
finally {
    kubectl delete pod $PodName -n $Namespace --ignore-not-found | Out-Null
}
