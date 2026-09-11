param(
    [switch]$Activate,
    [switch]$Rollback,
    [string]$RecoveryFile = "",
    [string]$Namespace = "forge-observability",
    [string]$Deployment = "prometheus",
    [string]$Service = "prometheus",
    [string]$ConfigMap = "prometheus-config",
    [string]$ExpectedContext = "kubernetes-admin@kubernetes",
    [int]$ExpectedTargetCount = 3,
    [int]$LocalPort = 19090,
    [int]$TimeoutSeconds = 180,
    [int]$HistoryHours = 24
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ($Activate -and $Rollback) {
    throw "Choose either -Activate or -Rollback, not both"
}

if ($Rollback -and -not $RecoveryFile) {
    throw "-Rollback requires the exact -RecoveryFile created before activation"
}

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptDir
$ManifestPath = Join-Path $RepoRoot "k8s/prometheus/prometheus-config.yaml"
$ExpectedImage = "prom/prometheus:v3.13.2"
$BaselineConfigHash = "070efd2b53a24a2df3acbe7782ee6c70886131b26bd8cacaaad27a3fbfff7507"
$CandidateConfigHash = "c5c2e613e3bc6575d4d1085382362627ccb0f94da5a1fc1ddc418463ad4525de"
$CandidateRuleHash = "2a52f3c16e254eff53fc3756dd695bb508b4b87909f82a7ae5e43ebebcda8040"
$ExpectedAlerts = @(
    "RestaurantNoHealthyScrapeTargets",
    "RestaurantScrapeCoverageDegraded"
)
$PortForward = $null
$Changed = $false

function Invoke-Kubectl {
    param([string[]]$Arguments)

    $Output = & kubectl @Arguments 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "kubectl $($Arguments -join ' ') failed: $($Output | Out-String)"
    }
    return $Output
}

function Get-NormalizedHash {
    param([AllowEmptyString()][string]$Text)

    $Normalized = $Text.Replace("`r`n", "`n").TrimEnd("`r", "`n") + "`n"
    $Bytes = [Text.Encoding]::UTF8.GetBytes($Normalized)
    $Hasher = [Security.Cryptography.SHA256]::Create()
    try {
        return ([BitConverter]::ToString($Hasher.ComputeHash($Bytes))).Replace("-", "").ToLowerInvariant()
    }
    finally {
        $Hasher.Dispose()
    }
}

function Get-LiveConfigMap {
    $Json = Invoke-Kubectl @("get", "configmap", $ConfigMap, "-n", $Namespace, "-o", "json")
    return (($Json | Out-String) | ConvertFrom-Json)
}

function Get-ConfigState {
    param($LiveConfigMap)

    $ConfigHash = Get-NormalizedHash ([string]$LiveConfigMap.data.'prometheus.yml')
    $HasRules = $LiveConfigMap.data.PSObject.Properties.Name -contains "restaurant-scrape.rules.yaml"
    $RuleHash = if ($HasRules) {
        Get-NormalizedHash ([string]$LiveConfigMap.data.'restaurant-scrape.rules.yaml')
    }
    else { "absent" }

    if ($ConfigHash -eq $BaselineConfigHash -and -not $HasRules) { return "baseline" }
    if ($ConfigHash -eq $CandidateConfigHash -and $RuleHash -eq $CandidateRuleHash) { return "candidate" }
    return "unexpected (prometheus.yml=$ConfigHash, rules=$RuleHash)"
}

function Assert-ContextAndWorkload {
    param([bool]$RequireReady)

    $Context = ((Invoke-Kubectl @("config", "current-context")) | Out-String).Trim()
    if ($Context -ne $ExpectedContext) {
        throw "Wrong Kubernetes context: '$Context'; expected '$ExpectedContext'"
    }

    $Json = Invoke-Kubectl @("get", "deployment", $Deployment, "-n", $Namespace, "-o", "json")
    $Object = (($Json | Out-String) | ConvertFrom-Json)
    if ($Object.spec.template.spec.containers[0].image -ne $ExpectedImage) {
        throw "Unexpected Prometheus image; expected $ExpectedImage"
    }
    if ($Object.spec.replicas -ne 1) {
        throw "Expected one configured Prometheus replica before continuing"
    }
    if ($RequireReady -and $Object.status.readyReplicas -ne 1) {
        throw "Expected one ready Prometheus replica before planning or activation"
    }
}

function Start-PrometheusAccess {
    if ($script:PortForward -and -not $script:PortForward.HasExited) { return }

    $script:PortForward = Start-Process -FilePath "kubectl" `
        -ArgumentList @("port-forward", "-n", $Namespace, "service/$Service", "${LocalPort}:9090") `
        -PassThru -WindowStyle Hidden
    $Deadline = (Get-Date).AddSeconds(30)
    do {
        try {
            Invoke-RestMethod -Uri "http://127.0.0.1:$LocalPort/-/ready" -TimeoutSec 2 | Out-Null
            return
        }
        catch {
            if ($script:PortForward.HasExited) {
                throw "Prometheus port-forward exited before readiness"
            }
            Start-Sleep -Seconds 1
        }
    } while ((Get-Date) -lt $Deadline)

    throw "Timed out waiting for the local Prometheus port-forward"
}

function Stop-PrometheusAccess {
    if ($script:PortForward -and -not $script:PortForward.HasExited) {
        Stop-Process -Id $script:PortForward.Id -Force -ErrorAction SilentlyContinue
        $script:PortForward.WaitForExit()
    }
    $script:PortForward = $null
}

function Enable-KubectlDiff {
    # Windows PowerShell defines `diff` as an alias for Compare-Object. Only an
    # external executable satisfies kubectl's diff subprocess requirement.
    if (Get-Command diff.exe -CommandType Application -ErrorAction SilentlyContinue) { return }

    $Candidates = @()
    $GitCommand = Get-Command git.exe -ErrorAction SilentlyContinue
    if (-not $GitCommand) {
        $GitCommand = Get-Command git -ErrorAction SilentlyContinue
    }
    if ($GitCommand) {
        $GitDirectory = Split-Path -Parent $GitCommand.Source
        $GitRoot = Split-Path -Parent $GitDirectory
        $Candidates += Join-Path $GitRoot "usr\bin\diff.exe"
    }
    if ($env:ProgramFiles) {
        $Candidates += Join-Path $env:ProgramFiles "Git\usr\bin\diff.exe"
    }

    $GitDiff = $Candidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
    if (-not $GitDiff) {
        throw "kubectl diff requires diff.exe. Git for Windows is installed, but its bundled usr\bin\diff.exe could not be found."
    }

    $DiffDirectory = Split-Path -Parent $GitDiff
    $env:PATH = "$DiffDirectory;$env:PATH"
    Write-Host "Using Git for Windows diff: $GitDiff"
}

function Invoke-PrometheusApi {
    param([string]$Path)
    return Invoke-RestMethod -Uri "http://127.0.0.1:$LocalPort$Path" -TimeoutSec 10
}

function Get-HealthyTargetCount {
    $Query = [Uri]::EscapeDataString('sum(up{job="restaurant-api",namespace="forge-restaurant"})')
    $Response = Invoke-PrometheusApi "/api/v1/query?query=$Query"
    if ($Response.status -ne "success" -or @($Response.data.result).Count -ne 1) {
        throw "Scoped healthy-target query returned no single result"
    }
    return [int][double]$Response.data.result[0].value[1]
}

function Get-LoadedAlerts {
    $Response = Invoke-PrometheusApi "/api/v1/rules?type=alert"
    if ($Response.status -ne "success") { throw "Prometheus rules API failed" }
    return @(
        $Response.data.groups |
            ForEach-Object { $_.rules } |
            Where-Object { $_.type -eq "alerting" } |
            Where-Object { $_.name -in $ExpectedAlerts }
    )
}

function Assert-LiveState {
    param([bool]$ExpectRules)

    Start-PrometheusAccess
    $Count = Get-HealthyTargetCount
    if ($Count -ne $ExpectedTargetCount) {
        throw "Expected $ExpectedTargetCount healthy Restaurant API targets; got $Count"
    }

    $Rules = @(Get-LoadedAlerts)
    if (-not $ExpectRules) {
        if ($Rules.Count -ne 0) { throw "SignalForge alert rules are unexpectedly loaded" }
        Write-Host "Live check: $Count healthy targets; candidate alerts not loaded."
        return
    }

    $Names = @($Rules | ForEach-Object { $_.name } | Sort-Object)
    if ($Names.Count -ne 2 -or (Compare-Object $ExpectedAlerts $Names)) {
        throw "Prometheus did not load exactly the two accepted alert rules"
    }
    foreach ($Rule in $Rules) {
        if ($Rule.health -ne "ok" -or $Rule.state -ne "inactive") {
            throw "Alert $($Rule.name) is health=$($Rule.health), state=$($Rule.state); expected ok/inactive"
        }
    }
    Write-Host "Live check: $Count healthy targets; both accepted alerts are loaded, healthy, and inactive."
}

function Show-CoverageHistory {
    $Query = [Uri]::EscapeDataString('sum(up{job="restaurant-api",namespace="forge-restaurant"})')
    $End = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
    $Start = $End - ($HistoryHours * 3600)
    $Response = Invoke-PrometheusApi "/api/v1/query_range?query=$Query&start=$Start&end=$End&step=30"
    $Series = @($Response.data.result)
    if ($Response.status -ne "success" -or $Series.Count -ne 1) {
        Write-Warning "No scoped history was returned; rollout timing still requires manual review."
        return
    }
    $Values = @($Series[0].values)
    $Counts = @($Values | ForEach-Object { [double]$_[1] })
    $Below = @($Counts | Where-Object { $_ -lt $ExpectedTargetCount }).Count
    $Minimum = ($Counts | Measure-Object -Minimum).Minimum
    $Longest = 0
    $Current = 0
    $PreviousTimestamp = $null
    foreach ($Point in $Values) {
        $Timestamp = [long]$Point[0]
        if ($PreviousTimestamp -and ($Timestamp - $PreviousTimestamp) -gt 45) { $Current = 0 }
        if ([double]$Point[1] -lt $ExpectedTargetCount) {
            $Current += 30
            if ($Current -gt $Longest) { $Longest = $Current }
        }
        else { $Current = 0 }
        $PreviousTimestamp = $Timestamp
    }
    Write-Host "History review (${HistoryHours}h, 30s samples): minimum=$Minimum; below-$ExpectedTargetCount samples=$Below/$($Counts.Count); longest contiguous sampled deficit=${Longest}s."
    Write-Host "This is context only: it does not validate availability, evaluator self-health, or notification delivery."
}

function Save-RecoveryConfigMap {
    param($LiveConfigMap)

    if ($RecoveryFile) {
        $Path = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($RecoveryFile)
    }
    else {
        $Base = Join-Path $env:USERPROFILE "SignalForge-Backups/prometheus"
        New-Item -ItemType Directory -Path $Base -Force | Out-Null
        $Path = Join-Path $Base ("alert-activation-{0}Z.json" -f (Get-Date).ToUniversalTime().ToString("yyyyMMdd-HHmmss"))
    }

    $Recovery = [ordered]@{
        apiVersion = "v1"
        kind = "ConfigMap"
        metadata = [ordered]@{
            name = $ConfigMap
            namespace = $Namespace
            labels = $LiveConfigMap.metadata.labels
        }
        data = $LiveConfigMap.data
    }
    $Recovery | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $Path -Encoding UTF8
    $Check = Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json
    if ((Get-ConfigState $Check) -ne "baseline") {
        throw "Recovery file did not preserve the accepted baseline ConfigMap"
    }
    return $Path
}

function Invoke-Rollback {
    param([string]$Path)

    $Resolved = (Resolve-Path -LiteralPath $Path).Path
    $Recovery = Get-Content -LiteralPath $Resolved -Raw | ConvertFrom-Json
    if ($Recovery.kind -ne "ConfigMap" -or $Recovery.metadata.name -ne $ConfigMap -or
        $Recovery.metadata.namespace -ne $Namespace -or (Get-ConfigState $Recovery) -ne "baseline") {
        throw "Recovery file is not the exact accepted baseline for $Namespace/$ConfigMap"
    }
    Invoke-Kubectl @("apply", "-f", $Resolved) | Write-Host
    Invoke-Kubectl @("rollout", "restart", "deployment/$Deployment", "-n", $Namespace) | Write-Host
    Invoke-Kubectl @("rollout", "status", "deployment/$Deployment", "-n", $Namespace, "--timeout=${TimeoutSeconds}s") | Write-Host
    Stop-PrometheusAccess
    Assert-LiveState $false
    Write-Host "Rollback verified. Recovery file retained at $Resolved"
}

Set-Location $RepoRoot
try {
    Assert-ContextAndWorkload (-not $Rollback)
    $Live = Get-LiveConfigMap
    $State = Get-ConfigState $Live
    Write-Host "Live Prometheus ConfigMap state: $State"

    if ($Rollback) {
        Invoke-Rollback $RecoveryFile
        return
    }

    Start-PrometheusAccess
    Assert-LiveState ($State -eq "candidate")
    Show-CoverageHistory

    Write-Host ""
    Write-Host "Server-side validation of the candidate manifest:"
    Invoke-Kubectl @("apply", "--dry-run=server", "-f", $ManifestPath, "-o", "name") | Write-Host

    Write-Host ""
    Write-Host "Candidate diff (kubectl diff exit code 1 means differences were found):"
    Enable-KubectlDiff
    & kubectl diff -f $ManifestPath
    $DiffExit = $LASTEXITCODE
    if ($DiffExit -gt 1) { throw "kubectl diff failed with exit code $DiffExit" }

    if (-not $Activate) {
        Write-Host ""
        Write-Host "PLAN ONLY: no cluster objects were changed."
        if ($State -eq "baseline") {
            Write-Host "After reviewing the history and diff, activation requires a separate explicit command:"
            Write-Host "powershell -ExecutionPolicy Bypass -File .\scripts\manage-prometheus-alerts.ps1 -Activate"
        }
        elseif ($State -eq "candidate") {
            Write-Host "The candidate is already active; this run only verified its current state."
        }
        else {
            Write-Warning "The live ConfigMap is not a recognized baseline or candidate; do not activate."
        }
        return
    }

    if ($State -ne "baseline") {
        throw "Activation is allowed only from the exact accepted baseline; live state is $State"
    }

    $SavedRecovery = Save-RecoveryConfigMap $Live
    Write-Host "Recovery ConfigMap saved and verified: $SavedRecovery"
    $Changed = $true
    Invoke-Kubectl @("apply", "-f", $ManifestPath) | Write-Host
    Invoke-Kubectl @("rollout", "restart", "deployment/$Deployment", "-n", $Namespace) | Write-Host
    Invoke-Kubectl @("rollout", "status", "deployment/$Deployment", "-n", $Namespace, "--timeout=${TimeoutSeconds}s") | Write-Host
    Stop-PrometheusAccess
    Assert-LiveState $true
    $Changed = $false
    Write-Host "Activation verified. No receiver exists; these alerts are visible only in Prometheus."
    Write-Host "Retain the rollback file: $SavedRecovery"
}
catch {
    $Failure = $_
    if ($Changed) {
        Write-Warning "Activation failed after mutation; attempting automatic rollback."
        try {
            Stop-PrometheusAccess
            Invoke-Rollback $SavedRecovery
        }
        catch {
            throw "Activation failed: $Failure Automatic rollback also failed: $_ Retain and apply $SavedRecovery manually."
        }
    }
    throw $Failure
}
finally {
    Stop-PrometheusAccess
}
