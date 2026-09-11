param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("status", "deploy", "smoke", "pods", "logs", "image", "nodes", "metrics-deploy", "metrics-status", "metrics-storage", "metrics-persistence", "metrics-backup-ready", "metrics-backup", "metrics-restore-test", "metrics-targets", "metrics-alerts-plan", "metrics-ui", "metrics-server-deploy", "metrics-server-status", "top")]
    [string]$Command,

    [string]$Namespace = "forge-restaurant",
    [string]$Deployment = "restaurant-api",
    [string]$Service = "restaurant-api",
    [string]$MetricsNamespace = "forge-observability",
    [string]$MetricsDeployment = "prometheus",
    [string]$MetricsService = "prometheus",
    [string]$BackupPath = "",
    [string]$MetricsServerNamespace = "kube-system",
    [string]$MetricsServerDeployment = "metrics-server"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptDir

function Show-Header {
    param([string]$Title)

    Write-Host ""
    Write-Host "=== $Title ==="
}

function Invoke-ClusterCurl {
    param(
        [string]$Endpoint
    )

    $Timestamp = Get-Date -Format "yyyyMMddHHmmssfff"
    $PodName = "curl-test-$Timestamp"
    $Url = "http://$Service$Endpoint"

    Show-Header "Smoke test $Url"

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
                kubectl logs $PodName -n $Namespace
                throw "Smoke test failed for $Url"
            }
        } while ((Get-Date) -lt $Deadline)

        if ($Phase -ne "Succeeded") {
            throw "Timed out waiting for smoke test pod $PodName"
        }

        kubectl logs $PodName -n $Namespace
    }
    finally {
        kubectl delete pod $PodName -n $Namespace --ignore-not-found | Out-Null
    }
}

switch ($Command) {
    "nodes" {
        Show-Header "Cluster nodes"
        kubectl get nodes -o wide
    }

    "status" {
        Show-Header "Current context"
        kubectl config current-context

        Show-Header "Cluster nodes"
        kubectl get nodes -o wide

        Show-Header "Restaurant namespace"
        kubectl get all -n $Namespace
    }

    "deploy" {
        Show-Header "Deploy Restaurant API"
        & "$ScriptDir\deploy-restaurant-api.ps1"
    }

    "smoke" {
        Invoke-ClusterCurl "/version"
        Invoke-ClusterCurl "/status"
    }

    "pods" {
        Show-Header "Restaurant API pods"
        kubectl get pods -n $Namespace -l app=$Deployment -o wide
    }

    "image" {
        Show-Header "Current deployed image"
        $CurrentImage = kubectl get deploy $Deployment -n $Namespace -o jsonpath="{.spec.template.spec.containers[0].image}"
        Write-Host $CurrentImage
    }

    "logs" {
        Show-Header "Recent Restaurant API logs"
        kubectl logs -n $Namespace -l app=$Deployment --tail=100
    }

    "metrics-deploy" {
        Show-Header "Deploy lightweight Prometheus"
        & "$ScriptDir\deploy-prometheus.ps1"
    }

    "metrics-status" {
        Show-Header "Prometheus resources"
        kubectl get deployment,pods,service -n $MetricsNamespace -l app=$MetricsDeployment -o wide

        Show-Header "Prometheus persistent storage"
        kubectl get storageclass signalforge-local-nvme
        kubectl get pv prometheus-local-nvme
        kubectl get pvc prometheus-data -n $MetricsNamespace

        Show-Header "Prometheus Pod-discovery permission"
        kubectl auth can-i list pods `
            -n $Namespace `
            --as=system:serviceaccount:${MetricsNamespace}:prometheus
    }

    "metrics-storage" {
        Show-Header "Prometheus persistent-storage validation"
        & "$ScriptDir\test-prometheus-storage.ps1" -Namespace $MetricsNamespace
    }

    "metrics-persistence" {
        Show-Header "Prometheus Pod-replacement persistence test"
        & "$ScriptDir\test-prometheus-persistence.ps1" -Namespace $MetricsNamespace
    }

    "metrics-backup-ready" {
        Show-Header "Prometheus acceptance-backup readiness"
        & "$ScriptDir\test-prometheus-backup-ready.ps1" -Namespace $MetricsNamespace
    }

    "metrics-backup" {
        Show-Header "Prometheus cold backup"
        & "$ScriptDir\backup-prometheus.ps1" -Namespace $MetricsNamespace
    }

    "metrics-restore-test" {
        Show-Header "Prometheus non-destructive restore validation"

        if ($BackupPath) {
            & "$ScriptDir\test-prometheus-restore.ps1" `
                -Namespace $MetricsNamespace `
                -BackupPath $BackupPath
        }
        else {
            & "$ScriptDir\test-prometheus-restore.ps1" -Namespace $MetricsNamespace
        }
    }

    "metrics-targets" {
        Show-Header "Prometheus Restaurant API targets"
        & "$ScriptDir\test-prometheus-targets.ps1" -Namespace $MetricsNamespace
    }

    "metrics-alerts-plan" {
        Show-Header "Prometheus limited-alerting activation plan"
        & "$ScriptDir\manage-prometheus-alerts.ps1" `
            -Namespace $MetricsNamespace `
            -Deployment $MetricsDeployment `
            -Service $MetricsService
    }

    "metrics-ui" {
        Show-Header "Prometheus UI"
        Write-Host "Open http://localhost:9090 in a browser."
        Write-Host "Press Ctrl+C here to stop the port-forward."
        kubectl port-forward `
            -n $MetricsNamespace `
            service/$MetricsService `
            9090:9090
    }

    "metrics-server-deploy" {
        Show-Header "Deploy Kubernetes Metrics Server"
        & "$ScriptDir\deploy-metrics-server.ps1"
    }

    "metrics-server-status" {
        Show-Header "Metrics APIService"
        kubectl get apiservice v1beta1.metrics.k8s.io

        Show-Header "Metrics Server workload"
        kubectl get deployment,pod `
            -n $MetricsServerNamespace `
            -l k8s-app=$MetricsServerDeployment `
            -o wide

        Show-Header "Metrics Server validation"
        & "$ScriptDir\test-metrics-server.ps1" `
            -Namespace $MetricsServerNamespace `
            -Deployment $MetricsServerDeployment
    }

    "top" {
        Show-Header "Cluster node usage"
        kubectl top nodes

        Show-Header "Restaurant API Pod usage"
        kubectl top pods -n $Namespace

        Show-Header "Prometheus Pod usage"
        kubectl top pods -n $MetricsNamespace

        Show-Header "Metrics Server Pod usage"
        kubectl top pod `
            -n $MetricsServerNamespace `
            -l k8s-app=$MetricsServerDeployment
    }
}
