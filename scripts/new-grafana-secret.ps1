param(
    [Parameter(Mandatory)][string]$ExpectedContext,
    [Parameter(Mandatory)][string]$RecoveryFile
)
. (Join-Path $PSScriptRoot 'grafana-common.ps1')
Assert-GrafanaContext -ExpectedContext $ExpectedContext
if ([Environment]::OSVersion.Platform -ne 'Win32NT') { throw 'Recovery export requires Windows DPAPI' }
$RecoveryFile = [IO.Path]::GetFullPath($RecoveryFile)
$Repository = [IO.Path]::GetFullPath((Split-Path $PSScriptRoot -Parent)).TrimEnd('\') + '\'
if ($RecoveryFile.StartsWith($Repository,[StringComparison]::OrdinalIgnoreCase)) { throw 'Store recovery credentials outside the repository' }
if (Test-Path -LiteralPath $RecoveryFile) { throw 'Recovery file already exists; will not overwrite' }
$Existing = Invoke-GrafanaKubectl -Arguments @('get','secret','grafana-admin','-n',$GrafanaNamespace,'--ignore-not-found','-o','name')
if ($Existing) { throw 'Secret exists; use the documented account rotation procedure instead' }
$User = Read-Host 'Bootstrap admin username'
if ([string]::IsNullOrWhiteSpace($User)) { throw 'Username is required' }
$Password = Read-Host 'Strong admin password (at least 20 characters, retained in your password manager)' -AsSecureString
if ($Password.Length -lt 20) { throw 'Use at least 20 characters' }
$Random = New-Object byte[] 48
$Rng = [Security.Cryptography.RandomNumberGenerator]::Create()
$Rng.GetBytes($Random)
$Rng.Dispose()
$Key = [Convert]::ToBase64String($Random)
$ProtectedKey = ConvertTo-SecureString $Key -AsPlainText -Force
$Recovery = [PSCustomObject]@{ Username=$User; Password=$Password; SecretKey=$ProtectedKey }
# On Windows, SecureString values are encrypted to this Windows user and machine.
$Recovery | Export-Clixml -LiteralPath $RecoveryFile
$Ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($Password)
try {
    $PlainPassword = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($Ptr)
    $Body = @{apiVersion='v1';kind='Secret';metadata=@{name='grafana-admin';namespace=$GrafanaNamespace};type='Opaque';stringData=@{'admin-user'=$User;'admin-password'=$PlainPassword;'secret-key'=$Key}} | ConvertTo-Json -Depth 8 -Compress
    $Body | & kubectl create -f -
    if ($LASTEXITCODE -ne 0) { throw 'Secret creation failed; encrypted recovery file has been retained' }
} finally {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($Ptr)
    $Body=$null; $PlainPassword=$null; $Key=$null; $Recovery=$null
    [Array]::Clear($Random,0,$Random.Length)
}
Write-Host 'Secret created. Recovery file is protected to this Windows user and machine; preserve an independent password-manager recovery copy before acceptance.'
