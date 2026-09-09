param(
    [string]$Namespace = "forge-observability",
    [string]$ManifestPath = "k8s/prometheus",
    [string]$Deployment = "prometheus",
    [string]$PersistentVolume = "prometheus-local-nvme",
    [string]$PersistentVolumeClaim = "prometheus-data",
    [string]$ExpectedNode = "forge-head",
    [int]$ExpectedTargetCount = 3,
    [int]$BindingTimeoutSeconds = 120
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
Write-Host "Checking the local-volume node and control-plane taint..."
$NodeJson = kubectl get node $ExpectedNode -o json

if ($LASTEXITCODE -ne 0 -or -not $NodeJson) {
    throw "Could not read expected local-volume node $ExpectedNode"
}

$Node = $NodeJson | Out-String | ConvertFrom-Json
$Hostname = $Node.metadata.labels.'kubernetes.io/hostname'

if ($Hostname -ne $ExpectedNode) {
    throw "Node $ExpectedNode does not have the expected kubernetes.io/hostname label"
}

$Taints = @()

if ($Node.spec.PSObject.Properties.Name -contains "taints") {
    $Taints = @($Node.spec.taints)
}

$HasControlPlaneTaint = @(
    $Taints | Where-Object {
        $_.key -eq "node-role.kubernetes.io/control-plane" -and
        $_.effect -eq "NoSchedule"
    }
).Count -gt 0

if (-not $HasControlPlaneTaint) {
    throw "Node $ExpectedNode is missing the expected control-plane NoSchedule taint; review scheduling before continuing"
}

Write-Host "Local-volume node and control-plane taint are present."

Write-Host ""
Write-Host "Creating the observability namespace..."
kubectl apply -f (Join-Path $ResolvedManifestPath "namespace.yaml")

if ($LASTEXITCODE -ne 0) {
    throw "Could not apply the observability namespace"
}

Write-Host ""
Write-Host "Applying persistent-storage manifests..."

$StorageManifestFiles = @(
    "prometheus-storage-class.yaml",
    "prometheus-local-pv.yaml",
    "prometheus-data-pvc.yaml"
)

foreach ($ManifestFile in $StorageManifestFiles) {
    kubectl apply -f (Join-Path $ResolvedManifestPath $ManifestFile)

    if ($LASTEXITCODE -ne 0) {
        throw "Could not apply $ManifestFile"
    }
}

Write-Host ""
Write-Host "Creating a temporary first consumer to bind and write-test the local volume..."
$PreflightPod = "prometheus-storage-preflight"
kubectl delete pod $PreflightPod -n $Namespace --ignore-not-found --wait=true | Out-Null

if ($LASTEXITCODE -ne 0) {
    throw "Could not remove a stale storage preflight Pod"
}

kubectl apply -f (Join-Path $ResolvedManifestPath "prometheus-storage-preflight-pod.yaml")

if ($LASTEXITCODE -ne 0) {
    throw "Could not create the storage preflight Pod"
}

Write-Host "Waiting for PVC $PersistentVolumeClaim to bind before replacing Prometheus storage..."
$BindingDeadline = (Get-Date).AddSeconds($BindingTimeoutSeconds)
$ClaimPhase = ""

do {
    $ClaimPhase = kubectl get pvc $PersistentVolumeClaim `
        -n $Namespace `
        -o "jsonpath={.status.phase}" 2>$null

    if ($LASTEXITCODE -eq 0 -and $ClaimPhase -eq "Bound") {
        break
    }

    Start-Sleep -Seconds 2
} while ((Get-Date) -lt $BindingDeadline)

if ($ClaimPhase -ne "Bound") {
    kubectl get pv $PersistentVolume -o wide
    kubectl get pvc $PersistentVolumeClaim -n $Namespace -o wide
    kubectl describe pod $PreflightPod -n $Namespace
    throw "PVC $Namespace/$PersistentVolumeClaim did not bind; the existing Prometheus Deployment was not changed"
}

$BoundVolume = kubectl get pvc $PersistentVolumeClaim `
    -n $Namespace `
    -o "jsonpath={.spec.volumeName}"

if ($LASTEXITCODE -ne 0 -or $BoundVolume -ne $PersistentVolume) {
    throw "PVC $Namespace/$PersistentVolumeClaim bound to '$BoundVolume' instead of $PersistentVolume; the existing Prometheus Deployment was not changed"
}

kubectl wait `
    -n $Namespace `
    --for=condition=Ready `
    "pod/$PreflightPod" `
    --timeout="${BindingTimeoutSeconds}s" | Out-Null

if ($LASTEXITCODE -ne 0) {
    kubectl describe pod $PreflightPod -n $Namespace
    kubectl logs $PreflightPod -n $Namespace
    throw "Storage preflight Pod did not become Ready; the existing Prometheus Deployment was not changed"
}

$PreflightNode = kubectl get pod $PreflightPod `
    -n $Namespace `
    -o "jsonpath={.spec.nodeName}"

if ($LASTEXITCODE -ne 0 -or $PreflightNode -ne $ExpectedNode) {
    throw "Storage preflight Pod ran on '$PreflightNode' instead of $ExpectedNode; the existing Prometheus Deployment was not changed"
}

kubectl delete pod $PreflightPod -n $Namespace --wait=true --timeout=60s | Out-Null

if ($LASTEXITCODE -ne 0) {
    throw "Storage preflight passed, but its temporary Pod could not be removed; the existing Prometheus Deployment was not changed"
}

Write-Host "PVC $Namespace/$PersistentVolumeClaim is bound to $PersistentVolume and passed its write test on $ExpectedNode."

Write-Host ""
Write-Host "Applying Prometheus workload manifests..."

$ManifestFiles = @(
    "prometheus-service-account.yaml",
    "restaurant-pod-reader-role.yaml",
    "restaurant-pod-reader-role-binding.yaml",
    "prometheus-config.yaml",
    "prometheus-service.yaml",
    "prometheus-deployment.yaml"
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
kubectl get storageclass signalforge-local-nvme
kubectl get pv $PersistentVolume
kubectl get pvc $PersistentVolumeClaim -n $Namespace

Write-Host ""
& "$ScriptDir\test-prometheus-storage.ps1" `
    -Namespace $Namespace `
    -PersistentVolume $PersistentVolume `
    -PersistentVolumeClaim $PersistentVolumeClaim `
    -ExpectedNode $ExpectedNode

Write-Host ""
& "$ScriptDir\test-prometheus-targets.ps1" `
    -Namespace $Namespace `
    -ExpectedTargetCount $ExpectedTargetCount `
    -TimeoutSeconds 120

Write-Host ""
Write-Host "Prometheus persistent-storage deployment and target checks completed successfully."
Write-Host "Run '.\scripts\forge.ps1 metrics-persistence' to verify that a known sample survives Pod replacement."
Write-Host "Run '.\scripts\forge.ps1 metrics-ui' to open the Prometheus UI."
