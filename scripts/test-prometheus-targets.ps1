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
$Query = "count(up{job=`"restaurant-api`"} == 1) == $ExpectedTargetCount"
$EncodedQuery = [uri]::EscapeDataString($Query)
$Url = "http://$Service.$Namespace.svc.cluster.local:9090/api/v1/query?query=$EncodedQuery"
$Attempts = [Math]::Max(1, [Math]::Ceiling($TimeoutSeconds / 5))

$CheckCommand = @'
last_response=""
i=0
while [ "$i" -lt __ATTEMPTS__ ]; do
  last_response=$(curl -fsS "__URL__") || last_response=""
  if echo "$last_response" | grep -q '"result":\[{' ; then
    echo "$last_response"
    exit 0
  fi
  i=$((i + 1))
  sleep 5
done
echo "$last_response"
exit 1
'@

$CheckCommand = $CheckCommand.Replace("__ATTEMPTS__", [string]$Attempts)
$CheckCommand = $CheckCommand.Replace("__URL__", $Url)

Write-Host "Waiting for $ExpectedTargetCount healthy Restaurant API Prometheus targets..."

try {
    kubectl run $PodName `
        -n $Namespace `
        --image=curlimages/curl:8.22.0 `
        --restart=Never `
        --command -- sh -c $CheckCommand | Out-Null

    if ($LASTEXITCODE -ne 0) {
        throw "Could not create Prometheus query Pod $PodName"
    }

    $Deadline = (Get-Date).AddSeconds($TimeoutSeconds + 30)
    $Phase = ""

    do {
        Start-Sleep -Seconds 1
        $Phase = kubectl get pod $PodName -n $Namespace -o "jsonpath={.status.phase}" 2>$null

        if ($Phase -eq "Succeeded" -or $Phase -eq "Failed") {
            break
        }
    } while ((Get-Date) -lt $Deadline)

    $Output = kubectl logs $PodName -n $Namespace 2>$null

    if ($Phase -ne "Succeeded") {
        if ($Output) {
            Write-Host $Output
        }

        if ($Phase -eq "Failed") {
            throw "Prometheus did not report $ExpectedTargetCount healthy Restaurant API targets within $TimeoutSeconds seconds"
        }

        throw "Timed out waiting for Prometheus query Pod $PodName"
    }

    $Response = $Output | ConvertFrom-Json
    $Result = $Response.data.result

    if (-not $Result -or $Result.Count -ne 1) {
        throw "Prometheus target query returned an unexpected result"
    }

    $TargetCount = [int]$Result[0].value[1]

    if ($TargetCount -ne $ExpectedTargetCount) {
        throw "Expected $ExpectedTargetCount healthy Restaurant API targets, but Prometheus reported $TargetCount"
    }

    Write-Host "Healthy Restaurant API targets: $TargetCount"
}
finally {
    kubectl delete pod $PodName -n $Namespace --ignore-not-found | Out-Null
}

