param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("status", "test", "validate-k8s", "deploy", "smoke", "preflight")]
    [string]$Command
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptDir
$RestaurantApiPath = Join-Path $RepoRoot "apps\restaurant-api"

function Show-Header {
    param([string]$Title)

    Write-Host ""
    Write-Host "=== $Title ==="
}

Set-Location $RepoRoot

switch ($Command) {
    "status" {
        Show-Header "Git status"
        git status

        Show-Header "Current branch"
        git branch --show-current

        Show-Header "Kubernetes context"
        kubectl config current-context

        Show-Header "Cluster nodes"
        kubectl get nodes -o wide

        Show-Header "Restaurant API resources"
        kubectl get all -n forge-restaurant
    }

    "test" {
        Show-Header "Restaurant API tests"
        Set-Location $RestaurantApiPath
        python -m pytest -q
        Set-Location $RepoRoot
    }

    "validate-k8s" {
        Show-Header "Kubernetes manifest validation"
        Set-Location $RepoRoot
        python .\scripts\validate-k8s-manifests.py
    }

    "deploy" {
        Show-Header "Restaurant API deployment"
        & "$ScriptDir\forge.ps1" deploy
    }

    "smoke" {
        Show-Header "Restaurant API smoke tests"
        & "$ScriptDir\forge.ps1" smoke
    }

    "preflight" {
        Show-Header "Developer preflight"

        Show-Header "Git status"
        git status

        Show-Header "Restaurant API tests"
        Set-Location $RestaurantApiPath
        python -m pytest -q

        Show-Header "Kubernetes manifest validation"
        Set-Location $RepoRoot
        python .\scripts\validate-k8s-manifests.py

        Show-Header "Kubernetes context"
        kubectl config current-context

        Show-Header "Restaurant API smoke tests"
        & "$ScriptDir\forge.ps1" smoke

        Show-Header "Preflight complete"
        Write-Host "All local checks passed."
    }
}
