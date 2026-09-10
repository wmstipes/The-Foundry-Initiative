param([Parameter(Mandatory)][string]$ExpectedContext)
. (Join-Path $PSScriptRoot 'grafana-common.ps1')
Assert-GrafanaContext -ExpectedContext $ExpectedContext
Write-Host 'Open http://127.0.0.1:3000 while this terminal remains running. Press Ctrl+C to close access.'
Invoke-GrafanaKubectl -Arguments @('port-forward','--address','127.0.0.1','-n',$GrafanaNamespace,'service/grafana','3000:3000')
