param(
    [string]$Namespace = "kube-system",
    [string]$ManifestPath = "k8s/metrics-server",
    [string]$Deployment = "metrics-server",
    [int]$ExpectedNodeCount = 4
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptDir
$ResolvedManifestPath = Join-Path $RepoRoot $ManifestPath

Set-Location $RepoRoot

Write-Host ""
Write-Host "SignalForge Kubernetes Metrics Server Deployment Helper"
Write-Host "Repo root: $RepoRoot"
Write-Host "Namespace: $Namespace"
Write-Host "Manifest path: $ManifestPath"
Write-Host ""

Write-Host "Current Kubernetes context:"
kubectl config current-context

if ($LASTEXITCODE -ne 0) {
    throw "kubectl does not have a working current context"
}

Write-Host ""
Write-Host "Applying Metrics Server manifests..."

$ManifestFiles = @(
    "metrics-server-service-account.yaml",
    "metrics-server-rbac.yaml",
    "metrics-server-service.yaml",
    "metrics-server-deployment.yaml",
    "metrics-server-api-service.yaml"
)

foreach ($ManifestFile in $ManifestFiles) {
    kubectl apply -f (Join-Path $ResolvedManifestPath $ManifestFile)

    if ($LASTEXITCODE -ne 0) {
        throw "Could not apply $ManifestFile"
    }
}

Write-Host ""
& "$ScriptDir\test-metrics-server.ps1" `
    -Namespace $Namespace `
    -Deployment $Deployment `
    -ExpectedNodeCount $ExpectedNodeCount `
    -TimeoutSeconds 120

Write-Host ""
Write-Host "Metrics Server deployment and validation completed successfully."
Write-Host "Run '.\scripts\forge.ps1 top' for current cluster resource usage."
