param(
    [string]$Namespace = "kube-system",
    [string]$Deployment = "metrics-server",
    [int]$ExpectedNodeCount = 4,
    [int]$TimeoutSeconds = 120
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ExpectedImage = "registry.k8s.io/metrics-server/metrics-server:v0.9.0"
$ExpectedCaArgument = "--kubelet-certificate-authority=/var/run/secrets/kubernetes.io/serviceaccount/ca.crt"
$Timeout = "$($TimeoutSeconds)s"

Write-Host "Validating the Metrics Server deployment..."

$DeploymentJson = kubectl get deployment $Deployment -n $Namespace -o json

if ($LASTEXITCODE -ne 0) {
    throw "Could not read the Metrics Server Deployment"
}

$DeploymentObject = ($DeploymentJson -join "`n") | ConvertFrom-Json
$Containers = @($DeploymentObject.spec.template.spec.containers)
$Container = $Containers | Where-Object { $_.name -eq $Deployment } | Select-Object -First 1

if ($null -eq $Container) {
    throw "Metrics Server container was not found in the Deployment"
}

if ($Container.image -ne $ExpectedImage) {
    throw "Expected Metrics Server image $ExpectedImage, but found $($Container.image)"
}

$Arguments = @($Container.args)

if ($Arguments -notcontains $ExpectedCaArgument) {
    throw "Metrics Server is not configured to validate kubelet certificates with the Kubernetes CA"
}

if ($Arguments -contains "--kubelet-insecure-tls") {
    throw "Metrics Server must not use --kubelet-insecure-tls"
}

Write-Host "Metrics Server uses the pinned image and secure kubelet CA validation."

kubectl rollout status deployment/$Deployment -n $Namespace --timeout=$Timeout

if ($LASTEXITCODE -ne 0) {
    throw "Metrics Server rollout did not complete"
}

kubectl wait `
    --for=condition=Available `
    apiservice/v1beta1.metrics.k8s.io `
    --timeout=$Timeout | Out-Null

if ($LASTEXITCODE -ne 0) {
    throw "The metrics.k8s.io APIService did not become available"
}

$Deadline = (Get-Date).AddSeconds($TimeoutSeconds)
$ReportedNodeCount = 0
$LastMetricsError = $null

do {
    $RawMetrics = kubectl get --raw "/apis/metrics.k8s.io/v1beta1/nodes" 2>$null

    if ($LASTEXITCODE -eq 0 -and $RawMetrics) {
        try {
            $MetricsObject = ($RawMetrics -join "`n") | ConvertFrom-Json
            $ReportedNodeCount = @($MetricsObject.items).Count

            if ($ReportedNodeCount -eq $ExpectedNodeCount) {
                break
            }
        }
        catch {
            $LastMetricsError = $_.Exception.Message
        }
    }

    Start-Sleep -Seconds 5
} while ((Get-Date) -lt $Deadline)

if ($ReportedNodeCount -ne $ExpectedNodeCount) {
    if ($LastMetricsError) {
        throw "Could not parse Metrics API output: $LastMetricsError"
    }

    throw "Expected metrics for $ExpectedNodeCount nodes, but received $ReportedNodeCount"
}

$PodJson = kubectl get pods `
    -n $Namespace `
    -l k8s-app=metrics-server `
    -o json

if ($LASTEXITCODE -ne 0) {
    throw "Could not list Metrics Server Pods"
}

$PodObject = ($PodJson -join "`n") | ConvertFrom-Json
$MetricsServerPod = @($PodObject.items) |
    Where-Object {
        $DeletionTimestamp = $_.metadata.PSObject.Properties["deletionTimestamp"]
        $ContainerStatuses = $_.status.PSObject.Properties["containerStatuses"]
        $ReadyContainers = @(
            if ($null -ne $ContainerStatuses) {
                $ContainerStatuses.Value |
                    Where-Object { $_.name -eq $Deployment -and $_.ready }
            }
        )

        $null -eq $DeletionTimestamp -and
            $_.status.phase -eq "Running" -and
            $ReadyContainers.Count -gt 0
    } |
    Sort-Object { [datetime]$_.metadata.creationTimestamp } -Descending |
    Select-Object -First 1

if ($null -eq $MetricsServerPod) {
    throw "Could not find a ready, non-terminating Metrics Server Pod"
}

$PodName = $MetricsServerPod.metadata.name
$RecentLogs = kubectl logs `
    -n $Namespace `
    "pod/$PodName" `
    --container $Deployment `
    --since=5m 2>$null

if ($LASTEXITCODE -ne 0) {
    throw "Could not read Metrics Server logs"
}

$ProblemLogs = @(
    $RecentLogs | Where-Object {
        $_ -match "x509|failed to scrape|unauthorized|forbidden"
    }
)

if ($ProblemLogs.Count -gt 0) {
    $ProblemLogs | ForEach-Object { Write-Host $_ }
    throw "Metrics Server reported a recent certificate, authorization, or scrape error"
}

Write-Host "Metrics API reports all $ReportedNodeCount SignalForge nodes."
Write-Host "No recent Metrics Server certificate, authorization, or scrape errors were found."

Write-Host ""
Write-Host "Current node usage:"
kubectl top nodes

if ($LASTEXITCODE -ne 0) {
    throw "kubectl top nodes failed"
}

Write-Host ""
Write-Host "Current Metrics Server usage:"
kubectl top pod -n $Namespace -l k8s-app=metrics-server

if ($LASTEXITCODE -ne 0) {
    throw "Could not read Metrics Server resource usage"
}

Write-Host ""
Write-Host "Metrics Server validation completed successfully."
