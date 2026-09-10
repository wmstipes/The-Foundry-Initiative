param([string]$SshTarget = 'wmstipes@192.168.243.110')
. (Join-Path $PSScriptRoot 'grafana-common.ps1')

Write-Host 'Read-only Grafana preflight; no deployment or disk changes'
Invoke-GrafanaKubectl -Arguments @('config','current-context')
Invoke-GrafanaKubectl -Arguments @('get','nodes','-o','wide')
Invoke-GrafanaKubectl -Arguments @('describe','node','forge-head')
Invoke-GrafanaKubectl -Arguments @('top','nodes')
Invoke-GrafanaKubectl -Arguments @('get','deployment,pods,services,pvc','-n',$GrafanaNamespace,'-o','wide')
Invoke-GrafanaKubectl -Arguments @('get','pv','prometheus-local-nvme','-o','yaml')
Invoke-GrafanaKubectl -Arguments @('get','storageclass','signalforge-local-nvme','-o','yaml')
Invoke-GrafanaKubectl -Arguments @('get','configmap','coredns','-n','kube-system','-o','yaml')
Invoke-GrafanaKubectl -Arguments @('get','networkpolicy','-A')
$HostChecks = @'
set -eu
hostname
uname -m
lsblk -o NAME,SIZE,TYPE,FSTYPE,MOUNTPOINTS,MODEL,SERIAL,UUID,PARTUUID
sudo -n sfdisk --dump /dev/nvme0n1
sudo -n sfdisk --list-free /dev/nvme0n1
sudo -n nvme smart-log /dev/nvme0n1
findmnt --mountpoint /mnt/signalforge-prometheus
df -h /mnt/signalforge-prometheus
sudo -n findmnt --verify
exit
'@
$HostChecks.Replace("`r",'') | & ssh -T -o BatchMode=yes -o StrictHostKeyChecking=yes $SshTarget "tr -d '\r' | bash -s"
if ($LASTEXITCODE -ne 0) { throw 'Host preflight failed; inspect SSH or sudo access before proceeding' }
Write-Host 'Preflight inventory complete. Review unused extents and drive health before preparing Grafana storage.'
