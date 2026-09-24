# Loki recovery candidate — source only

## Decision boundary

The accepted central logging rollout established ingestion, Grafana queries,
and retrieval of a known probe log after replacement of its source Pod. On
2026-09-24 the operator confirmed `loki-0` Ready with zero restarts, Alloy
Ready, the 8 GiB retained PV/PVC Bound, ext4 UUID
`93a19402-4a5b-4689-aed7-f1841c2cb53b` mounted read/write, 7.4 GiB free,
and 716 KiB in Loki's data directory. Grafana returned exactly one
`functional_check` for `sampleId=bfa2350926ed44d181678c02a4439ec0`
at 2026-09-24T14:44:08Z. This operator-provided baseline does not establish
Loki restart persistence, off-node recovery, or seven-day retention.

This candidate adds reviewable tooling. Source publication authorizes no
cluster mutation, logging interruption, archive creation, or cleanup. Review
the scripts, dry-run output, encrypted destination, and recovery commands
before a separately approved live gate.

## Backup contract

`scripts/loki-recovery.py backup` checks the exact context, one Ready Loki and
Alloy replica, pinned Loki image, head placement, zero Loki restarts, and the
Bound retained PV/PVC. Without `--execute`, it is read-only. The live path
requires `--encrypted-destination-verified` and an existing destination
outside Git. It stops Alloy first and Loki second, waits for both Pods to
exit, mounts the production PVC read-only in a restricted helper, streams a
complete `/var/loki` archive off-node, checks its structure, and records its
SHA-256 and image/config identity. It never rewrites the production PVC or
prunes older archives. A `.partial` file after an error must be inspected,
not used as a backup.
An archive lacking either sidecar after an interrupted write is also
incomplete and must not be used for restore.

The helper uses pinned BusyBox `1.37.0` OCI index
`sha256:bdf57e528e45e4433820e045b29b4597825a1c9e38353532d90a01445013f82e`
with Linux ARM64 child `sha256:d82c2ab94640ded77cf76514ce6a84870761105058a4a9e51b05a8a79be97a6c`
from Docker Hub's tag API on 2026-09-24. Verify availability during the live
image preflight.

The `finally` path removes only its helper and attempts to restore Loki
before Alloy, reporting incomplete recovery as an error. Keep the terminal
open and verify both a pre-backup and a fresh post-recovery sample. A pause
in collection is expected; lossless ingestion is not guaranteed.

## Restore contract

`scripts/loki-recovery.py restore` checks the off-node archive hash, safe
entries, image/config identity, live cluster baseline, and head NVMe UUID.
Without `--execute`, it creates nothing. The live path refuses an existing
restore directory, creates only `/mnt/signalforge-loki/restore-validation`,
streams the archive into a temporary extraction Pod, removes that Pod, then
creates a deny ingress/egress NetworkPolicy and a separate pinned Loki Pod.
The restored Pod mounts only the isolated host directory, never `loki-data`;
it has no Service or Alloy target and listens on 3101. Its isolation and
localhost port-forward must be checked during live acceptance; policy
enforcement depends on the CNI.

The restored Pod and directory remain for review. Query the exact pre-backup
sample ID through a localhost port-forward. Ready alone is not restore
acceptance. A failed restore leaves the isolated directory for inspection;
never rerun over that path. Cleanup of the named Pod, policy, and exact
directory is a later reviewed gate.

## Operator commands — proposed, not authorized live steps

From the repository root on the Windows laptop, first inspect the source,
server dry-run/diff each new Kubernetes manifest, and use the read-only plans:

```powershell
python .\scripts\loki-recovery.py backup --destination "$env:USERPROFILE\SignalForge-Backups\loki"
python .\scripts\loki-recovery.py restore --archive '<verified archive path>'
```

The explicit live commands, after separate approval and verifying the off-node
destination is encrypted and protected, are:

```powershell
python .\scripts\loki-recovery.py backup --destination "$env:USERPROFILE\SignalForge-Backups\loki" --encrypted-destination-verified --execute
python .\scripts\loki-recovery.py restore --archive '<verified archive path>' --execute
```

After an isolated restore Pod becomes Ready, forward its port in a separate
terminal with `kubectl -n forge-observability port-forward --address 127.0.0.1
pod/loki-restore-validation 13101:3101`. Query its `/loki/api/v1/query_range`
over that localhost port for the marker within 2026-09-24 14:40–14:50 UTC.
For example, in another PowerShell terminal:

```powershell
$query = '{namespace="forge-pulse",container="service-pulse-probe"} |= "bfa2350926ed44d181678c02a4439ec0"'
curl.exe --get 'http://127.0.0.1:13101/loki/api/v1/query_range' --data-urlencode "query=$query" --data-urlencode 'start=2026-09-24T14:40:00Z' --data-urlencode 'end=2026-09-24T14:50:00Z'
```

Grafana's normal datasource still points to production Loki and cannot
validate this restored copy. Keep the restored resources until the result
has been reviewed.

## Acceptance and limitations

1. Offline: Python compilation, archive-safety tests, YAML parsing, and
   repository validation pass. Compare manifests and script to this contract.
2. Live backup: exact context/image verified; interruption recorded;
   archive/hash sidecars present off-node; Loki and Alloy Ready afterward;
   historical and new sample IDs returned by production Loki.
3. Isolated restore: checksum verified; restored pinned Loki Ready; old
   sample returned through localhost; production Loki healthy. Record the
   elapsed recovery time. Listing or extracting an archive alone is not
   service recovery.
4. Retention: follow a dated marker beyond 168h plus the configured 2h
   deletion delay; distinguish query invisibility from chunk deletion.
   Do not shorten retention or inject backdated logs to accelerate this check.

Filesystem storage on one NVMe is not resilient to loss of `forge-head`.
The archive may contain sensitive log text; keep it off-node and protected,
not in the repository or PR.
