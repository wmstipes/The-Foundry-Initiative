#!/usr/bin/env bash
# Run interactively on forge-head. Default is read-only; --prepare requires the
# SHA-256 of a matching sfdisk dump already copied and verified off-node.
set -euo pipefail
export LC_ALL=C

device=/dev/nvme0n1
partition=/dev/nvme0n1p3
mount_dir=/mnt/signalforge-loki
start=75499520
sectors=16777216
end=92276735
mode="${1:---plan}"
case "$mode" in
  --plan) test "$#" -le 1 || { echo 'Usage: sudo bash prepare-loki-storage.sh --plan' >&2; exit 2; } ;;
  --prepare) test "$#" -eq 2 && [[ "$2" =~ ^[a-fA-F0-9]{64}$ ]] || { echo 'Usage: sudo bash prepare-loki-storage.sh --prepare OFF_NODE_SFDISK_SHA256' >&2; exit 2; } ;;
  *) echo 'Usage: sudo bash prepare-loki-storage.sh --plan|--prepare OFF_NODE_SFDISK_SHA256' >&2; exit 2 ;;
esac
test "$(id -u)" -eq 0
test "$(hostname)" = forge-head
test "$(lsblk -dn -o MODEL "$device" | xargs)" = 'Samsung SSD 950 PRO 512GB'
test "$(lsblk -dn -o SERIAL "$device" | xargs)" = S2GMNCAGB06236R
test "$(blockdev --getss "$device")" = 512
test "$(findmnt -n -o UUID --mountpoint /mnt/signalforge-prometheus)" = 4f2feee5-72a7-4f32-a351-b4253c4a0854
test "$(findmnt -n -o UUID --mountpoint /mnt/signalforge-grafana)" = a506c674-127a-46da-9c7d-d158b6d1bb75
test "$(blkid -s UUID -o value /dev/nvme0n1p1)" = 4f2feee5-72a7-4f32-a351-b4253c4a0854
test "$(blkid -s UUID -o value /dev/nvme0n1p2)" = a506c674-127a-46da-9c7d-d158b6d1bb75
test ! -e "$partition"
test ! -e "$mount_dir"
if grep -q 'signalforge-loki' /etc/fstab; then echo 'Loki fstab entry already exists; stop' >&2; exit 1; fi
for tool in sfdisk partx udevadm mkfs.ext4 blkid findmnt mount umount setpriv python3 nvme; do command -v "$tool" >/dev/null; done

sfdisk --json "$device" | python3 -c '
import json,sys
t=json.load(sys.stdin)["partitiontable"]
assert t["label"] == "gpt" and t["id"].upper() == "FDF2C7FC-C23E-4147-93B5-B53D85A08F78" and t["sectorsize"] == 512
assert len(t["partitions"]) == 2 and t["lastlba"] >= 92276735
p1,p2=t["partitions"]
assert (p1["node"],p1["start"],p1["size"],p1["uuid"].upper()) == ("/dev/nvme0n1p1",2048,67108864,"4811522E-21C3-4FAE-AE0D-835AC0299FC3")
assert (p2["node"],p2["start"],p2["size"],p2["uuid"].upper()) == ("/dev/nvme0n1p2",67110912,8388608,"A8E50BC1-1B9C-419B-A13D-3EE72C29FF56")
assert p2["start"] + p2["size"] == 75499520
'
nvme smart-log "$device" -o json | python3 -c '
import json,sys
d=json.load(sys.stdin); w=d["critical_warning"]; w=w["value"] if isinstance(w,dict) else w
assert int(w)==0 and int(d["avail_spare"])>=99 and int(d["media_errors"])==215
'
entry='start=75499520, size=16777216, type=0FC63DAF-8483-4772-8E79-3D69D8477DE4, name="signalforge-loki"'
echo "Verified drive and existing mounts. Candidate p3: sectors $start-$end (8 GiB)."
sfdisk --list-free "$device"
printf '%s\n' "$entry" | sfdisk --no-act --append --no-reread --no-tell-kernel --wipe never --wipe-partitions never "$device"
if [[ "$mode" = --plan ]]; then
  echo 'PLAN ONLY: no partition, filesystem, mount or fstab change.'
  exit 0
fi

current_hash=$(sfdisk --dump "$device" | sha256sum | cut -d' ' -f1)
if [[ "$current_hash" != "${2,,}" ]]; then echo 'Partition table differs from off-node backup; stop' >&2; exit 1; fi
backup_dir=$(mktemp -d /var/tmp/signalforge-loki-storage.XXXXXX)
sfdisk --dump "$device" > "$backup_dir/before.sfdisk"
cp -p /etc/fstab "$backup_dir/fstab.before"
trap 'rc=$?; if [[ "$rc" -ne 0 ]]; then echo "STOP: partial preparation may exist. Do not rerun or format. Inspect $backup_dir and off-node backup." >&2; fi' EXIT
printf '%s\n' "$entry" | sfdisk --lock --append --no-reread --no-tell-kernel --wipe never --wipe-partitions never "$device"
sfdisk --dump "$device" > "$backup_dir/after.sfdisk"
for n in 1 2; do diff <(grep "^/dev/nvme0n1p$n " "$backup_dir/before.sfdisk") <(grep "^/dev/nvme0n1p$n " "$backup_dir/after.sfdisk"); done
sfdisk --json "$device" | python3 -c 'import json,sys;t=json.load(sys.stdin)["partitiontable"];assert len(t["partitions"])==3;p=t["partitions"][2];assert (p["node"],p["start"],p["size"],p["name"]) == ("/dev/nvme0n1p3",75499520,16777216,"signalforge-loki")'
partx --add --nr 3 "$device"
udevadm settle
test -b "$partition"
test "$(cat /sys/class/block/nvme0n1p3/start)" = "$start"
test "$(cat /sys/class/block/nvme0n1p3/size)" = "$sectors"
test "$(blockdev --getsize64 "$partition")" = 8589934592
if findmnt -rn -S "$partition" >/dev/null; then echo 'Partition unexpectedly mounted; stop' >&2; exit 1; fi
set +e
probe=$(blkid -p --no-part-details -o export "$partition" 2>&1)
probe_rc=$?
set -e
if { test "$probe_rc" != 0 && test "$probe_rc" != 2; } || test -n "$probe"; then echo "Unexpected partition signature (exit $probe_rc): $probe" >&2; exit 1; fi
mkfs.ext4 -E nodiscard -L sf-loki "$partition"
uuid=$(blkid -s UUID -o value "$partition")
test -n "$uuid"
install -d -m 0755 "$mount_dir"
mount -o noatime "UUID=$uuid" "$mount_dir"
test "$(findmnt -n -o UUID --mountpoint "$mount_dir")" = "$uuid"
install -d -o 10001 -g 10001 -m 0750 "$mount_dir/data"
setpriv --reuid=10001 --regid=10001 --clear-groups sh -ec 'f=$(mktemp /mnt/signalforge-loki/data/.write-check.XXXXXX); printf "verified\n" > "$f"; test -s "$f"; rm "$f"'
sync
umount "$mount_dir"
test ! -e "$mount_dir/data"
mount -o noatime "UUID=$uuid" "$mount_dir"
test "$(findmnt -n -o UUID --mountpoint "$mount_dir")" = "$uuid"
printf '\nUUID=%s /mnt/signalforge-loki ext4 defaults,noatime 0 2\n' "$uuid" >> /etc/fstab
systemctl daemon-reload
findmnt --verify
test "$(findmnt -n -o UUID --mountpoint /mnt/signalforge-prometheus)" = 4f2feee5-72a7-4f32-a351-b4253c4a0854
test "$(findmnt -n -o UUID --mountpoint /mnt/signalforge-grafana)" = a506c674-127a-46da-9c7d-d158b6d1bb75
echo "LOKI_FILESYSTEM_UUID=$uuid"
echo "HOST_EVIDENCE=$backup_dir"
echo 'Loki storage prepared; no Kubernetes objects created.'
