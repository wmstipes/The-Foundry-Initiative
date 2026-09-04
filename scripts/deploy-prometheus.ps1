param(
    [string]$Namespace = "forge-observability",
    [string]$ManifestPath = "k8s/prometheus",
    [string]$Deployment = "prometheus",
    [int]$ExpectedTargetCount = 3
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptDir
$ResolvedManifestPath = Join-Path $RepoRoot $ManifestPath

Set-Location $RepoRoot

Write-Host ""
Write-Host "SignalForge Lightweight Prometheus Deployment Helper"
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
Write-Host "Creating the observability namespace..."
kubectl apply -f (Join-Path $ResolvedManifestPath "namespace.yaml")

if ($LASTEXITCODE -ne 0) {
    throw "Could not apply the observability namespace"
}

Write-Host ""
Write-Host "Applying Prometheus manifests..."

$ManifestFiles = @(
    "prometheus-service-account.yaml",
    "restaurant-pod-reader-role.yaml",
    "restaurant-pod-reader-role-binding.yaml",
    "prometheus-config.yaml",
    "prometheus-deployment.yaml",
    "prometheus-service.yaml"
)

foreach ($ManifestFile in $ManifestFiles) {
    kubectl apply -f (Join-Path $ResolvedManifestPath $ManifestFile)

    if ($LASTEXITCODE -ne 0) {
        throw "Could not apply $ManifestFile"
    }
}

Write-Host ""
Write-Host "Checking Prometheus Pod-discovery permission..."
$CanListPods = kubectl auth can-i list pods `
    -n forge-restaurant `
    --as=system:serviceaccount:${Namespace}:prometheus

if ($LASTEXITCODE -ne 0 -or $CanListPods.Trim() -ne "yes") {
    throw "Prometheus ServiceAccount cannot list Pods in forge-restaurant"
}

Write-Host "Prometheus can list Pods in forge-restaurant."

Write-Host ""
Write-Host "Waiting for Prometheus rollout..."
kubectl rollout status deployment/$Deployment -n $Namespace --timeout=180s

if ($LASTEXITCODE -ne 0) {
    throw "Prometheus rollout did not complete"
}

Write-Host ""
Write-Host "Current Prometheus resources:"
kubectl get deployment,pods,service -n $Namespace -l app=prometheus -o wide

Write-Host ""
& "$ScriptDir\test-prometheus-targets.ps1" `
    -Namespace $Namespace `
    -ExpectedTargetCount $ExpectedTargetCount `
    -TimeoutSeconds 120

Write-Host ""
Write-Host "Prometheus deployment and target checks completed successfully."
Write-Host "Run '.\scripts\forge.ps1 metrics-ui' to open the Prometheus UI."

