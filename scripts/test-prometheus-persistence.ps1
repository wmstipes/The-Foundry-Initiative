param(
    [string]$Namespace = "forge-observability",
    [string]$Deployment = "prometheus",
    [string]$Service = "prometheus",
    [int]$TimeoutSeconds = 180
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Timestamp = Get-Date -Format "yyyyMMddHHmmssfff"
$QueryPodName = "prometheus-persistence-$Timestamp"
$QueryPodLifetimeSeconds = [Math]::Max(300, $TimeoutSeconds + 120)
$BaseUrl = "http://$Service.$Namespace.svc.cluster.local:9090/api/v1/query"

function Invoke-PrometheusQuery {
    param(
        [string]$Query,
        [string]$EvaluationTime = ""
    )

    $EncodedQuery = [uri]::EscapeDataString($Query)
    $Url = "$BaseUrl`?query=$EncodedQuery"

    if ($EvaluationTime) {
        $Url += "&time=$EvaluationTime"
    }

    $Output = kubectl exec -n $Namespace $QueryPodName -- curl -fsS $Url

    if ($LASTEXITCODE -ne 0 -or -not $Output) {
        throw "Could not query Prometheus"
    }

    $Response = $Output | Out-String | ConvertFrom-Json

    if ($Response.status -ne "success") {
        throw "Prometheus query did not succeed"
    }

    return $Response
}

Write-Host "This check deliberately replaces the Prometheus Pod after recording a known metric sample."
Write-Host "The retained local PV and PVC are not deleted."

try {
    kubectl run $QueryPodName `
        -n $Namespace `
        --image=curlimages/curl:8.22.0 `
        --restart=Never `
        --command -- sleep $QueryPodLifetimeSeconds | Out-Null

    if ($LASTEXITCODE -ne 0) {
        throw "Could not create Prometheus query Pod $QueryPodName"
    }

    kubectl wait `
        -n $Namespace `
        --for=condition=Ready `
        "pod/$QueryPodName" `
        --timeout=60s | Out-Null

    if ($LASTEXITCODE -ne 0) {
        throw "Prometheus query Pod $QueryPodName did not become ready"
    }

    $InitialResponse = Invoke-PrometheusQuery 'up{job="restaurant-api"} == 1'
    $InitialResults = @($InitialResponse.data.result)

    if ($InitialResults.Count -lt 1) {
        throw "Prometheus did not return a healthy Restaurant API sample to preserve"
    }

    $KnownPod = $InitialResults[0].metric.pod
    $KnownValue = [string]$InitialResults[0].value[1]
    $KnownTime = ([double]$InitialResults[0].value[0]).ToString(
        "0.###",
        [System.Globalization.CultureInfo]::InvariantCulture
    )

    if (-not $KnownPod -or $KnownValue -ne "1") {
        throw "The selected Restaurant API sample was not a healthy target sample"
    }

    $PrometheusPodJson = kubectl get pods -n $Namespace -l app=prometheus -o json

    if ($LASTEXITCODE -ne 0 -or -not $PrometheusPodJson) {
        throw "Could not read the current Prometheus Pod"
    }

    $PrometheusPods = @(($PrometheusPodJson | Out-String | ConvertFrom-Json).items)

    if ($PrometheusPods.Count -ne 1) {
        throw "Expected exactly one Prometheus Pod, found $($PrometheusPods.Count)"
    }

    $OldPodName = $PrometheusPods[0].metadata.name
    $OldPodUid = $PrometheusPods[0].metadata.uid

    Write-Host "Recorded sample: up{job=restaurant-api,pod=$KnownPod} = 1 at $KnownTime"
    Write-Host "Deleting Prometheus Pod $OldPodName..."
    kubectl delete pod $OldPodName -n $Namespace --wait=true --timeout=60s | Out-Null

    if ($LASTEXITCODE -ne 0) {
        throw "Could not delete Prometheus Pod $OldPodName"
    }

    $Deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    $NewPod = $null

    do {
        $PodJson = kubectl get pods -n $Namespace -l app=prometheus -o json 2>$null

        if ($LASTEXITCODE -eq 0 -and $PodJson) {
            $CandidatePods = @(($PodJson | Out-String | ConvertFrom-Json).items)

            if ($CandidatePods.Count -eq 1 -and $CandidatePods[0].metadata.uid -ne $OldPodUid) {
                $ReadyConditions = @(
                    $CandidatePods[0].status.conditions | Where-Object {
                        $_.type -eq "Ready" -and $_.status -eq "True"
                    }
                )

                if ($CandidatePods[0].status.phase -eq "Running" -and $ReadyConditions.Count -eq 1) {
                    $NewPod = $CandidatePods[0]
                    break
                }
            }
        }

        Start-Sleep -Seconds 3
    } while ((Get-Date) -lt $Deadline)

    if ($null -eq $NewPod) {
        throw "A replacement Prometheus Pod did not become Ready within $TimeoutSeconds seconds"
    }

    $HistoricalQuery = "up{job=`"restaurant-api`",pod=`"$KnownPod`"}"
    $HistoricalResponse = Invoke-PrometheusQuery $HistoricalQuery $KnownTime
    $HistoricalResults = @($HistoricalResponse.data.result)

    if ($HistoricalResults.Count -ne 1 -or [string]$HistoricalResults[0].value[1] -ne "1") {
        throw "The known sample was not present after Prometheus Pod replacement"
    }

    Write-Host "Replacement Pod: $($NewPod.metadata.name)"
    Write-Host "Recovered sample: up{job=restaurant-api,pod=$KnownPod} = 1 at $KnownTime"
    Write-Host "PASS: a known Prometheus sample survived Pod replacement."
}
finally {
    kubectl delete pod $QueryPodName -n $Namespace --ignore-not-found | Out-Null
}
