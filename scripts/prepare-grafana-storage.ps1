param(
    [string]$SshTarget = 'wmstipes@192.168.243.110',
    [string]$PrometheusBackup = "$env:USERPROFILE\SignalForge-Backups\prometheus\prometheus-tsdb-20260910-150206Z.tar.gz",
    [string]$ExpectedPrometheusBackupSha256 = '68e00637d6fd05db21bc8e5dbefa7bbb7d65a7548dd3de0eec5c2faae574dc24',
    [string]$EvidenceRoot = "$env:USERPROFILE\SignalForge-Backups\storage",
    [switch]$Prepare
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Read-StorageHost {
    param([string]$Command)
    $Result = & ssh -T -o BatchMode=yes -o StrictHostKeyChecking=yes $SshTarget $Command
    if ($LASTEXITCODE -ne 0) { throw 'SSH storage read failed; nothing has been partitioned' }
    return ($Result -join "`n") + "`n"
}

# No write phase is attempted until the accepted off-node TSDB backup verifies.
if (-not (Test-Path -LiteralPath $PrometheusBackup -PathType Leaf)) { throw "Required off-node Prometheus backup missing: $PrometheusBackup" }
if ((Get-FileHash -LiteralPath $PrometheusBackup -Algorithm SHA256).Hash.ToLowerInvariant() -ne $ExpectedPrometheusBackupSha256.ToLowerInvariant()) {
    throw 'Prometheus backup checksum mismatch'
}
if ($ExpectedPrometheusBackupSha256 -notmatch '^[a-fA-F0-9]{64}$') { throw 'Invalid expected backup checksum' }
$Stamp = [DateTime]::UtcNow.ToString('yyyyMMdd-HHmmssZ')
$EvidenceDirectory = Join-Path ([IO.Path]::GetFullPath($EvidenceRoot)) "grafana-$Stamp"
if (Test-Path -LiteralPath $EvidenceDirectory) { throw 'Evidence directory already exists; will not overwrite' }
[IO.Directory]::CreateDirectory($EvidenceDirectory) | Out-Null
$Utf8 = New-Object Text.UTF8Encoding($false)
$Table = Read-StorageHost 'sudo -n sfdisk --dump /dev/nvme0n1'
$TablePath = Join-Path $EvidenceDirectory 'nvme-before.sfdisk'
[IO.File]::WriteAllText($TablePath,$Table,$Utf8)
$RemoteHash = (Read-StorageHost 'sudo -n sfdisk --dump /dev/nvme0n1 | sha256sum').Trim().Split(' ')[0]
$TableHash = (Get-FileHash -LiteralPath $TablePath -Algorithm SHA256).Hash.ToLowerInvariant()
if ($TableHash -ne $RemoteHash) { throw 'Off-node partition-table backup did not match the source' }
[IO.File]::WriteAllText((Join-Path $EvidenceDirectory 'fstab-before.txt'),(Read-StorageHost 'cat /etc/fstab'),$Utf8)
$Inventory = Read-StorageHost 'sudo -n sfdisk --json /dev/nvme0n1'
[IO.File]::WriteAllText((Join-Path $EvidenceDirectory 'partitions-before.json'),$Inventory,$Utf8)
$Partitions = ($Inventory | ConvertFrom-Json).partitiontable
if ($Partitions.label -ne 'gpt' -or $Partitions.id -ne 'FDF2C7FC-C23E-4147-93B5-B53D85A08F78' -or $Partitions.sectorsize -ne 512 -or @($Partitions.partitions).Count -ne 1) {
    throw 'Partition inventory differs from reviewed layout; stop for review'
}
$First = $Partitions.partitions[0]
if ($First.node -ne '/dev/nvme0n1p1' -or $First.start -ne 2048 -or $First.size -ne 67108864 -or $First.uuid -ne '4811522E-21C3-4FAE-AE0D-835AC0299FC3') {
    throw 'Prometheus partition differs from reviewed layout'
}
Write-Host "Verified Prometheus archive and saved partition table off-node: $EvidenceDirectory"
Write-Host 'Exact allocation: /dev/nvme0n1p2; start 67110912; size 8388608 sectors; end 75499519; 4 GiB.'
Write-Host 'Preserve /dev/nvme0n1p1, its UUID and active Prometheus mount.'
if (-not $Prepare) {
    Write-Host 'Backup-only phase complete. Supply -Prepare to create and mount the approved Grafana partition.'
    return
}

$HostScript = @'
set -euo pipefail
export LC_ALL=C
dev=/dev/nvme0n1
part=/dev/nvme0n1p2
mount_dir=/mnt/signalforge-grafana
expected_table_hash=__TABLE_HASH__
test "$(hostname)" = forge-head
test "$(lsblk -dn -o SERIAL "$dev" | xargs)" = S2GMNCAGB06236R
test "$(lsblk -dn -o MODEL "$dev" | xargs)" = 'Samsung SSD 950 PRO 512GB'
test "$(blockdev --getss "$dev")" = 512
test "$(findmnt -n -o UUID --mountpoint /mnt/signalforge-prometheus)" = 4f2feee5-72a7-4f32-a351-b4253c4a0854
test "$(blkid -s UUID -o value /dev/nvme0n1p1)" = 4f2feee5-72a7-4f32-a351-b4253c4a0854
test "$(sfdisk --dump "$dev" | sha256sum | cut -d' ' -f1)" = "$expected_table_hash"
test ! -e "$part"
test ! -e "$mount_dir"
if grep -q 'signalforge-grafana' /etc/fstab; then echo 'Grafana fstab entry already exists; stop' >&2; exit 1; fi
for tool in sfdisk partx udevadm mkfs.ext4 blkid findmnt mount umount setpriv python3 nvme; do command -v "$tool" >/dev/null; done
nvme smart-log "$dev" -o json | python3 -c 'import json,sys; d=json.load(sys.stdin); c=d["critical_warning"]; c=c["value"] if isinstance(c,dict) else c; assert int(c)==0, "NVMe critical warning"; assert int(d["media_errors"])==215, "NVMe media-error count changed"; assert int(d["avail_spare"])>=99, "NVMe spare capacity below baseline"'
sfdisk --json "$dev" | python3 -c 'import json,sys; t=json.load(sys.stdin)["partitiontable"]; assert t["label"]=="gpt" and t["id"].upper()=="FDF2C7FC-C23E-4147-93B5-B53D85A08F78" and t["sectorsize"]==512; assert len(t["partitions"])==1; p=t["partitions"][0]; assert p["node"]=="/dev/nvme0n1p1" and p["start"]==2048 and p["size"]==67108864 and p["uuid"].upper()=="4811522E-21C3-4FAE-AE0D-835AC0299FC3"; assert t["lastlba"]>=75499519'
# Store an additional host copy; the verified NUC copy already exists.
backup_dir=$(mktemp -d /var/tmp/signalforge-grafana-storage.XXXXXX)
sfdisk --dump "$dev" > "$backup_dir/before.sfdisk"
cp -p /etc/fstab "$backup_dir/fstab.before"
trap 'rc=$?; if [ "$rc" -ne 0 ]; then echo "STOP: partial preparation may exist. Do not rerun or format again. Inspect $backup_dir and the NUC evidence." >&2; fi' EXIT
entry='start=67110912, size=8388608, type=0FC63DAF-8483-4772-8E79-3D69D8477DE4, name="signalforge-grafana"'
printf '%s\n' "$entry" | sfdisk --no-act --append --no-reread --no-tell-kernel --wipe never --wipe-partitions never "$dev"
# Append only; do not rewrite the existing partition or globally reread an in-use disk.
printf '%s\n' "$entry" | sfdisk --lock --append --no-reread --no-tell-kernel --wipe never --wipe-partitions never "$dev"
sfdisk --dump "$dev" > "$backup_dir/after.sfdisk"
diff <(grep '^/dev/nvme0n1p1 ' "$backup_dir/before.sfdisk") <(grep '^/dev/nvme0n1p1 ' "$backup_dir/after.sfdisk")
sfdisk --json "$dev" | python3 -c 'import json,sys; t=json.load(sys.stdin)["partitiontable"]; assert len(t["partitions"])==2; p=next(p for p in t["partitions"] if p["node"]=="/dev/nvme0n1p2"); assert p["start"]==67110912 and p["size"]==8388608 and p["name"]=="signalforge-grafana"'
partx --add --nr 2 "$dev"
udevadm settle
test -b "$part"
test "$(cat /sys/class/block/nvme0n1p2/start)" = 67110912
test "$(cat /sys/class/block/nvme0n1p2/size)" = 8388608
test "$(blockdev --getsize64 "$part")" = 4294967296
if findmnt -rn -S "$part" >/dev/null; then echo 'New partition is unexpectedly mounted' >&2; exit 1; fi
set +e
probe_output=$(blkid -p --no-part-details -o export "$part" 2>&1)
probe_rc=$?
set -e
if { test "$probe_rc" != 0 && test "$probe_rc" != 2; } || test -n "$probe_output"; then
    printf 'STOP: filesystem/signature probe needs review (exit %s): %s\n' "$probe_rc" "$probe_output" >&2
    exit 1
fi
# Never force a format over a detected signature; format only this newly verified extent.
mkfs.ext4 -E nodiscard -L sf-grafana "$part"
uuid=$(blkid -s UUID -o value "$part")
test -n "$uuid"
install -d -m 0755 "$mount_dir"
mount -o noatime "UUID=$uuid" "$mount_dir"
test "$(findmnt -n -o UUID --mountpoint "$mount_dir")" = "$uuid"
install -d -o 472 -g 0 -m 0750 "$mount_dir/data"
setpriv --reuid=472 --regid=0 --clear-groups sh -ec 'f=$(mktemp /mnt/signalforge-grafana/data/.write-check.XXXXXX); printf "verified\n" > "$f"; test -s "$f"; rm "$f"'
sync
umount "$mount_dir"
test ! -e "$mount_dir/data"
mount -o noatime "UUID=$uuid" "$mount_dir"
test "$(findmnt -n -o UUID --mountpoint "$mount_dir")" = "$uuid"
printf '\nUUID=%s /mnt/signalforge-grafana ext4 defaults,noatime 0 2\n' "$uuid" >> /etc/fstab
systemctl daemon-reload
findmnt --verify
test "$(blkid -s UUID -o value /dev/nvme0n1p1)" = 4f2feee5-72a7-4f32-a351-b4253c4a0854
test "$(findmnt -n -o UUID --mountpoint /mnt/signalforge-prometheus)" = 4f2feee5-72a7-4f32-a351-b4253c4a0854
nvme smart-log "$dev" -o json | python3 -c 'import json,sys; d=json.load(sys.stdin); c=d["critical_warning"]; c=c["value"] if isinstance(c,dict) else c; assert int(c)==0, "NVMe critical warning"; assert int(d["media_errors"])==215, "NVMe media-error count changed"; assert int(d["avail_spare"])>=99, "NVMe spare capacity below baseline"'
sfdisk --dump "$dev"
findmnt --mountpoint "$mount_dir"
stat -c '%u:%g %a %n' "$mount_dir/data"
df -h "$mount_dir"
printf 'GRAFANA_FILESYSTEM_UUID=%s\n' "$uuid"
printf 'HOST_EVIDENCE=%s\n' "$backup_dir"
printf 'Grafana storage prepared; no Kubernetes objects were created.\n'
exit
'@
$HostScript = $HostScript.Replace('__TABLE_HASH__',$TableHash)
# PowerShell's native pipeline can append CRLF even to an LF-normalized string.
# Remove CR remotely before Bash reads stdin; no host verification is bypassed.
$SavedPreference = $ErrorActionPreference
try {
    # Windows PowerShell can wrap harmless native stderr as ErrorRecord objects.
    # Capture them without aborting before we can check SSH's actual exit status.
    $ErrorActionPreference = 'Continue'
    $HostOutput = $HostScript.Replace("`r",'') | & ssh -T -o BatchMode=yes -o StrictHostKeyChecking=yes $SshTarget "tr -d '\r' | sudo -n bash -s" 2>&1
    $HostExit = $LASTEXITCODE
} finally {
    $ErrorActionPreference = $SavedPreference
}
$HostOutput | Tee-Object -FilePath (Join-Path $EvidenceDirectory 'preparation-output.txt')
if ($HostExit -ne 0) { throw 'Storage preparation stopped. Keep all evidence; do not rerun after a partial write. Return the output for review.' }
Write-Host "Storage preparation evidence: $EvidenceDirectory"
Write-Host 'Return the Grafana filesystem UUID and output for verification before deployment.'
