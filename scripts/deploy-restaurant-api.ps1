param(
    [string]$Namespace = "forge-restaurant",
    [string]$ManifestPath = "k8s/fastapi-restaurant",
    [string]$Deployment = "restaurant-api",
    [string]$Service = "restaurant-api"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptDir

Set-Location $RepoRoot

Write-Host ""
Write-Host "SignalForge Restaurant API Deployment Helper"
Write-Host "Repo root: $RepoRoot"
Write-Host "Namespace: $Namespace"
Write-Host "Manifest path: $ManifestPath"
Write-Host ""

Write-Host "Current Kubernetes context:"
kubectl config current-context

Write-Host ""
Write-Host "Applying Kubernetes manifests..."
kubectl apply -f $ManifestPath

Write-Host ""
Write-Host "Waiting for rollout..."
kubectl rollout status deployment/$Deployment -n $Namespace

Write-Host ""
Write-Host "Current pods:"
kubectl get pods -n $Namespace -l app=$Deployment -o wide

Write-Host ""
Write-Host "Current deployed image:"
$CurrentImage = kubectl get deploy $Deployment -n $Namespace -o jsonpath="{.spec.template.spec.containers[0].image}"
Write-Host $CurrentImage

function Invoke-ClusterCurl {
    param(
        [string]$Endpoint
    )

    $Timestamp = Get-Date -Format "yyyyMMddHHmmssfff"
    $PodName = "curl-test-$Timestamp"
    $Url = "http://$Service$Endpoint"

    Write-Host ""
    Write-Host "Smoke test: $Url"

    try {
        kubectl run $PodName `
            -n $Namespace `
            --image=curlimages/curl:latest `
            --restart=Never `
            --command -- curl -s $Url | Out-Null

        $Deadline = (Get-Date).AddSeconds(120)
        $Phase = ""

        do {
            Start-Sleep -Seconds 1
            $Phase = kubectl get pod $PodName -n $Namespace -o "jsonpath={.status.phase}" 2>$null

            if ($Phase -eq "Succeeded") {
                break
            }

            if ($Phase -eq "Failed") {
                Write-Host "Smoke test pod failed. Logs:"
                kubectl logs $PodName -n $Namespace
                throw "Smoke test failed for $Url"
            }
        } while ((Get-Date) -lt $Deadline)

        if ($Phase -ne "Succeeded") {
            throw "Timed out waiting for smoke test pod $PodName"
        }

        $Output = kubectl logs $PodName -n $Namespace
        Write-Host $Output

        return $Output
    }
    finally {
        kubectl delete pod $PodName -n $Namespace --ignore-not-found | Out-Null
    }
}

$VersionOutput = Invoke-ClusterCurl "/version"
Invoke-ClusterCurl "/status" | Out-Null

Write-Host ""
Write-Host "Deployment helper completed successfully."
Write-Host ""
