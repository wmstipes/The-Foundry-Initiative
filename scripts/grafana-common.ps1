Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$GrafanaNamespace = 'forge-observability'
$GrafanaManifestPath = Join-Path (Split-Path $PSScriptRoot -Parent) 'k8s/grafana'

function Invoke-GrafanaKubectl {
    param([Parameter(Mandatory)][string[]]$Arguments)
    $Result = & kubectl @Arguments
    if ($LASTEXITCODE -ne 0) { throw "kubectl failed: $($Arguments[0]) $($Arguments[1])" }
    return $Result
}

function Assert-GrafanaContext {
    param([Parameter(Mandatory)][string]$ExpectedContext)
    $Actual = (Invoke-GrafanaKubectl -Arguments @('config','current-context') | Out-String).Trim()
    if ($Actual -ne $ExpectedContext) { throw "Wrong context: $Actual; expected $ExpectedContext" }
    $Node = Invoke-GrafanaKubectl -Arguments @('get','node','forge-head','-o','json') | ConvertFrom-Json
    if ($Node.status.nodeInfo.architecture -ne 'arm64') { throw 'forge-head is not ARM64' }
    if (-not ($Node.status.conditions | Where-Object { $_.type -eq 'Ready' -and $_.status -eq 'True' })) {
        throw 'forge-head is not Ready'
    }
}

function Assert-GrafanaMount {
    param([Parameter(Mandatory)][string]$ExpectedFilesystemUuid,
          [string]$SshTarget = 'wmstipes@192.168.243.110')
    if ($ExpectedFilesystemUuid -notmatch '^[0-9a-fA-F-]{36}$') { throw 'Expected a filesystem UUID' }
    if ($ExpectedFilesystemUuid -eq '4f2feee5-72a7-4f32-a351-b4253c4a0854') {
        throw 'Refusing the Prometheus filesystem UUID'
    }
    $Actual = & ssh -o BatchMode=yes -o StrictHostKeyChecking=yes $SshTarget findmnt -n -o UUID --mountpoint /mnt/signalforge-grafana
    if ($LASTEXITCODE -ne 0 -or ($Actual | Out-String).Trim() -ne $ExpectedFilesystemUuid) {
        throw 'Grafana mount identity did not match; no Kubernetes writes performed'
    }
    & ssh -o BatchMode=yes -o StrictHostKeyChecking=yes $SshTarget test -d /mnt/signalforge-grafana/data
    if ($LASTEXITCODE -ne 0) { throw 'Grafana data directory is missing' }
}
