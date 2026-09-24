#!/usr/bin/env python3
"""Guarded operator-side cold backup and isolated Loki restore candidate.

Live subcommands require --execute; see k8s/central-logging/README.md.
"""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tarfile
from datetime import datetime, timezone
from time import monotonic, sleep


NAMESPACE = "forge-observability"
CONTEXT = "kubernetes-admin@kubernetes"
IMAGE = "grafana/loki:3.7.0@sha256:c316b7c7589a5eeca843b6926c7446149d18300b79ac8538dc4ae063bc478da2"
UUID = "93a19402-4a5b-4689-aed7-f1841c2cb53b"
RESTORE_PATH = "/mnt/signalforge-loki/restore-validation"
ROOT = Path(__file__).resolve().parent.parent
MANIFESTS = ROOT / "k8s" / "central-logging"


def command(*args, input_file=None, output_file=None):
    result = subprocess.run(args, stdin=input_file, stdout=output_file or subprocess.PIPE,
                            stderr=subprocess.PIPE, check=False)
    if result.returncode:
        error = result.stderr.decode("utf-8", "replace").strip()
        raise RuntimeError(f"{' '.join(args)} failed ({result.returncode}): {error}")
    return result.stdout.decode("utf-8", "replace").strip() if output_file is None else ""


def kubectl(*args):
    return command("kubectl", "--context", CONTEXT, *args)


def get(kind, name):
    return json.loads(kubectl("-n", NAMESPACE, "get", kind, name, "-o", "json"))


def preflight():
    actual = command("kubectl", "config", "current-context")
    if actual != CONTEXT:
        raise RuntimeError(f"Refusing context {actual!r}; expected {CONTEXT}")
    stateful = get("statefulset", "loki")
    alloy = get("deployment", "pulse-alloy")
    pvc = get("pvc", "loki-data")
    pv = json.loads(kubectl("get", "pv", "loki-local-nvme", "-o", "json"))
    pod = get("pod", "loki-0")
    if (stateful["spec"].get("replicas") != 1 or
            alloy["spec"].get("replicas") != 1 or
            stateful.get("status", {}).get("readyReplicas") != 1 or
            alloy.get("status", {}).get("availableReplicas") != 1):
        raise RuntimeError("Loki and Alloy must each have one configured and ready replica")
    if stateful["spec"]["template"]["spec"]["containers"][0]["image"] != IMAGE:
        raise RuntimeError("Live Loki image differs from reviewed candidate")
    template = stateful["spec"]["template"]["spec"]
    if not any(v.get("name") == "data" and v.get("persistentVolumeClaim", {}).get("claimName") == "loki-data"
               for v in template.get("volumes", [])) or not any(
                   m.get("name") == "data" and m.get("mountPath") == "/var/loki"
                   for m in template["containers"][0].get("volumeMounts", [])):
        raise RuntimeError("Live Loki data mount differs from reviewed candidate")
    if (pod["spec"].get("nodeName") != "forge-head" or
            pod["status"].get("phase") != "Running" or
            pod["status"]["containerStatuses"][0]["restartCount"] != 0):
        raise RuntimeError("Loki placement/status/restart baseline changed")
    if (pvc["status"].get("phase") != "Bound" or
            pvc["spec"].get("volumeName") != "loki-local-nvme" or
            pv["spec"]["local"]["path"] != "/mnt/signalforge-loki/data" or
            pv["spec"]["claimRef"]["name"] != "loki-data" or
            pv["spec"]["persistentVolumeReclaimPolicy"] != "Retain"):
        raise RuntimeError("Production Loki volume identity changed")
    existing = json.loads(kubectl("-n", NAMESPACE, "get", "pod", "-l", "app=loki-backup", "-o", "json"))
    if existing["items"]:
        raise RuntimeError("Existing Loki backup Pod must be reviewed before proceeding")
    print("PASS: expected context, ready workloads, image, placement and retained volume")


def verify_head_mount(host):
    if host not in ("forge-head", "192.168.243.110"):
        raise RuntimeError("Unexpected SSH host")
    mount = command("ssh", host, "findmnt", "-n", "-o", "UUID,FSTYPE,SOURCE",
                    "--mountpoint", "/mnt/signalforge-loki")
    if UUID not in mount or "ext4" not in mount or "/dev/nvme0n1p3" not in mount:
        raise RuntimeError("Loki NVMe filesystem identity changed")


def wait_absent(label, timeout=180):
    deadline = monotonic() + timeout
    while monotonic() < deadline:
        pods = json.loads(kubectl("-n", NAMESPACE, "get", "pods", "-l", label, "-o", "json"))
        if not pods["items"]:
            return
        sleep(2)
    raise RuntimeError(f"Timed out waiting for {label} Pods to stop")


def validate_archive(path):
    with tarfile.open(path, "r:gz") as archive:
        members = archive.getmembers()
        if not members:
            raise RuntimeError("Empty archive")
        for member in members:
            name = member.name.removeprefix("./")
            if member.name in (".", "./") and member.isdir():
                continue
            if (name.startswith("/") or "\\" in name or
                    any(part in ("", "..") for part in name.split("/")) or
                    not (member.isfile() or member.isdir())):
                raise RuntimeError(f"Unsafe archive entry: {member.name!r}")
        if not any(m.name.removeprefix("./").startswith("wal/") for m in members):
            raise RuntimeError("No WAL entry in complete-data archive")
    return len(members)


def backup(args):
    preflight()
    verify_head_mount(args.ssh_host)
    if not args.execute:
        print("PLAN ONLY: stop Alloy, stop Loki, mount PVC read-only in one helper Pod, "
              "stream complete archive off-node, then restore Loki and Alloy")
        return
    if not args.encrypted_destination_verified:
        raise RuntimeError("Confirm a protected encrypted off-node destination before --execute")
    destination = Path(args.destination).resolve()
    if destination == ROOT or ROOT in destination.parents or not destination.is_dir():
        raise RuntimeError("Destination must be an existing directory outside the repository")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%SZ")
    archive = destination / f"loki-cold-{stamp}.tar.gz"
    partial = destination / f"loki-cold-{stamp}.tar.gz.partial"
    if archive.exists() or partial.exists():
        raise RuntimeError("Timestamped destination already exists")
    attempted_alloy = attempted_loki = helper_created = False
    primary_error = None
    try:
        attempted_alloy = True
        kubectl("-n", NAMESPACE, "scale", "deployment/pulse-alloy", "--replicas=0")
        wait_absent("app=pulse-alloy")
        attempted_loki = True
        kubectl("-n", NAMESPACE, "scale", "statefulset/loki", "--replicas=0")
        wait_absent("app=loki")
        manifest = MANIFESTS / "loki-backup-pod.yaml"
        kubectl("create", "-f", str(manifest))
        helper_created = True
        kubectl("-n", NAMESPACE, "wait", "--for=condition=Ready", "pod/loki-backup", "--timeout=180s")
        helper = get("pod", "loki-backup")
        if helper["spec"].get("nodeName") != "forge-head":
            raise RuntimeError("Backup helper scheduled away from forge-head")
        with partial.open("xb") as output:
            command("kubectl", "--context", CONTEXT, "-n", NAMESPACE,
                    "exec", "loki-backup", "--", "tar", "-C", "/var/loki", "-czf", "-", ".",
                    output_file=output)
        entries = validate_archive(partial)
        if not partial.stat().st_size:
            raise RuntimeError("Empty backup stream")
        with partial.open("rb") as source:
            digest = hashlib.file_digest(source, "sha256").hexdigest()
        partial.rename(archive)
        (destination / f"{archive.name}.sha256").write_text(f"{digest}  {archive.name}\n", encoding="ascii")
        metadata = {"createdUtc": stamp, "sha256": digest, "bytes": archive.stat().st_size,
                    "entries": entries, "image": IMAGE, "sourceContext": CONTEXT,
                    "filesystemUuid": UUID,
                    "configSha256": hashlib.sha256((MANIFESTS / "loki-config.yaml").read_bytes()).hexdigest(),
                    "restoreVerified": False}
        (destination / f"{archive.name}.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
        print(f"Verified off-node archive: {archive}\nSHA-256: {digest}")
    except BaseException as exc:
        primary_error = exc
    finally:
        failures = []
        if helper_created:
            try:
                kubectl("-n", NAMESPACE, "delete", "pod", "loki-backup", "--wait=true", "--timeout=120s")
            except Exception as exc:
                failures.append(str(exc))
        if attempted_loki:
            try:
                kubectl("-n", NAMESPACE, "scale", "statefulset/loki", "--replicas=1")
                kubectl("-n", NAMESPACE, "rollout", "status", "statefulset/loki", "--timeout=180s")
            except Exception as exc:
                failures.append(f"LOKI RECOVERY: {exc}")
        if attempted_alloy:
            try:
                kubectl("-n", NAMESPACE, "scale", "deployment/pulse-alloy", "--replicas=1")
                kubectl("-n", NAMESPACE, "rollout", "status", "deployment/pulse-alloy", "--timeout=180s")
            except Exception as exc:
                failures.append(f"ALLOY RECOVERY: {exc}")
        if failures:
            raise RuntimeError("Recovery incomplete; inspect workloads immediately: " + "; ".join(failures)) from primary_error
    if primary_error:
        raise primary_error
    print("Workloads Ready. Verify old and new sample IDs in Grafana; backup integrity alone is not recovery acceptance.")


def restore(args):
    path = Path(args.archive).resolve()
    if not path.is_file():
        raise RuntimeError("Backup archive missing")
    expected = path.with_name(path.name + ".sha256")
    if not expected.is_file():
        raise RuntimeError("Checksum sidecar missing")
    tokens = expected.read_text(encoding="ascii").split()
    if len(tokens) != 2 or tokens[1] != path.name or len(tokens[0]) != 64 or any(c not in "0123456789abcdef" for c in tokens[0].lower()):
        raise RuntimeError("Invalid checksum sidecar")
    with path.open("rb") as source:
        digest = hashlib.file_digest(source, "sha256").hexdigest()
    if digest != tokens[0].lower():
        raise RuntimeError("Off-node archive checksum mismatch")
    metadata_path = path.with_name(path.name + ".json")
    if not metadata_path.is_file():
        raise RuntimeError("Backup metadata sidecar missing")
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    if (metadata.get("sha256") != digest or metadata.get("image") != IMAGE or
            metadata.get("filesystemUuid") != UUID or
            metadata.get("configSha256") != hashlib.sha256((MANIFESTS / "loki-config.yaml").read_bytes()).hexdigest()):
        raise RuntimeError("Backup metadata does not match archive/image/configuration")
    entries = validate_archive(path)
    preflight()
    verify_head_mount(args.ssh_host)
    if not args.execute:
        print(f"PLAN ONLY: {entries} safe archive entries; create {RESTORE_PATH}, extract into "
              "isolated Pod, run pinned Loki on port 3101; production PVC remains untouched")
        return
    absent = subprocess.run(("ssh", args.ssh_host, "test", "!", "-e", RESTORE_PATH), check=False)
    if absent.returncode:
        raise RuntimeError("Restore path exists or SSH check failed; inspect manually; no overwrite")
    for name in ("loki-restore-extract", "loki-restore-validation"):
        pods = json.loads(kubectl("-n", NAMESPACE, "get", "pod", "-l", f"app={name}", "-o", "json"))
        if pods["items"]:
            raise RuntimeError(f"Existing {name} Pod must be reviewed")
    command("ssh", "-t", args.ssh_host, "sudo", "install", "-d", "-o", "10001", "-g", "10001", "-m", "0750", RESTORE_PATH)
    extract_created = False
    try:
        kubectl("create", "-f", str(MANIFESTS / "loki-restore-extract-pod.yaml"))
        extract_created = True
        kubectl("-n", NAMESPACE, "wait", "--for=condition=Ready", "pod/loki-restore-extract", "--timeout=180s")
        with path.open("rb") as source:
            command("kubectl", "--context", CONTEXT, "-n", NAMESPACE, "exec", "-i",
                    "loki-restore-extract", "--", "tar", "-C", "/validation", "-xzf", "-",
                    input_file=source)
    finally:
        if extract_created:
            kubectl("-n", NAMESPACE, "delete", "pod", "loki-restore-extract", "--wait=true", "--timeout=120s")
    kubectl("create", "-f", str(MANIFESTS / "loki-restore-networkpolicy.yaml"))
    kubectl("create", "-f", str(MANIFESTS / "loki-restore-validation-pod.yaml"))
    kubectl("-n", NAMESPACE, "wait", "--for=condition=Ready", "pod/loki-restore-validation", "--timeout=180s")
    print("Isolated Loki Ready. Port-forward pod/loki-restore-validation 13101:3101 and query "
          "the original sample ID. Keep the Pod and restored directory for review; do not mark restore verified yet.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    backup_parser = sub.add_parser("backup")
    backup_parser.add_argument("--destination", required=True)
    backup_parser.add_argument("--execute", action="store_true")
    backup_parser.add_argument("--ssh-host", default="192.168.243.110")
    backup_parser.add_argument("--encrypted-destination-verified", action="store_true")
    restore_parser = sub.add_parser("restore")
    restore_parser.add_argument("--archive", required=True)
    restore_parser.add_argument("--ssh-host", default="192.168.243.110")
    restore_parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    try:
        (backup if args.action == "backup" else restore)(args)
    except Exception as exc:
        print(f"STOP: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
