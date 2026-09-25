"""Update only the Istio lab dashboard in the live Grafana ConfigMap.

Run on the operator's laptop. The default is read-only; --execute writes a
local backup, server-validates the replacement, and updates one ConfigMap.
"""

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTEXT = "kubernetes-admin@kubernetes"
NAMESPACE = "forge-observability"
NAME = "grafana-dashboards"
KEY = "signalforge-istio-lab.json"
REVIEW_HEAD = "e6785cb7fb2553bc99a8a90923aa3cbdd30914f3"
PREVIOUS_HEAD = "c216415939128af99d5760bdc1145ae29300b995"
SOURCE = ROOT / "k8s" / "grafana" / "dashboards" / KEY


def run(*args: str) -> str:
    result = subprocess.run(args, capture_output=True, text=True, timeout=90, check=False)
    if result.returncode:
        raise RuntimeError(f"{' '.join(args[:3])} failed: {result.stderr.strip()}")
    return result.stdout


def checked_live_config() -> tuple[dict, dict]:
    try:
        run("git", "-C", str(ROOT), "merge-base", "--is-ancestor", REVIEW_HEAD, "HEAD")
    except RuntimeError as exc:
        raise RuntimeError("Review checkout does not include the approved dashboard revision") from exc
    if run("kubectl", "config", "current-context").strip() != CONTEXT:
        raise RuntimeError("Kubernetes context differs")

    live = json.loads(run("kubectl", "--context", CONTEXT, "-n", NAMESPACE,
                          "get", f"configmap/{NAME}", "-o", "json"))
    if live.get("immutable") or live.get("binaryData"):
        raise RuntimeError("Unexpected immutable or binary ConfigMap; stop")
    if live["metadata"]["name"] != NAME or live["metadata"]["namespace"] != NAMESPACE:
        raise RuntimeError("Unexpected ConfigMap identity; stop")
    if not live["metadata"].get("resourceVersion"):
        raise RuntimeError("ConfigMap resourceVersion is missing; stop")

    previous = json.loads(run("git", "-C", str(ROOT), "show",
                              f"{PREVIOUS_HEAD}:k8s/grafana/dashboards/{KEY}"))
    candidate_dashboard = json.loads(SOURCE.read_text(encoding="utf-8"))
    current_dashboard = json.loads(live["data"][KEY])
    if current_dashboard == candidate_dashboard:
        print("ALREADY CURRENT: Grafana lab dashboard matches the reviewed revision")
        return live, candidate_dashboard
    if current_dashboard != previous:
        raise RuntimeError("Live lab dashboard differs from the reviewed previous version; stop")
    if candidate_dashboard["panels"][3]["title"] != "Client 503 responses (total)":
        raise RuntimeError("Reviewed dashboard has an unexpected 503 panel; stop")
    return live, candidate_dashboard


def replacement_for(live: dict, dashboard_source: str) -> dict:
    metadata = live["metadata"]
    return {
        "apiVersion": "v1",
        "kind": "ConfigMap",
        "metadata": {key: metadata[key] for key in
                     ("name", "namespace", "resourceVersion", "labels", "annotations")
                     if key in metadata},
        "data": {**live["data"], KEY: dashboard_source},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true", help="apply the validated one-key update")
    args = parser.parse_args()
    live, candidate_dashboard = checked_live_config()
    if json.loads(live["data"][KEY]) == candidate_dashboard:
        return
    if not args.execute:
        print("PLAN ONLY: replace one Grafana dashboard key; keep all other ConfigMap data")
        return

    directory = Path.home() / "SignalForge-Istio-Review"
    directory.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%fZ")
    backup = directory / f"grafana-dashboards-before-503-fix-{stamp}.json"
    with backup.open("x", encoding="utf-8") as stream:
        json.dump(live, stream, indent=2, ensure_ascii=False)
    candidate = directory / f"grafana-dashboards-503-fix-{stamp}.json"
    with candidate.open("x", encoding="utf-8") as stream:
        json.dump(replacement_for(live, SOURCE.read_text(encoding="utf-8")),
                  stream, indent=2, ensure_ascii=False)

    run("kubectl", "--context", CONTEXT, "replace", "--dry-run=server", "-f", str(candidate))
    run("kubectl", "--context", CONTEXT, "replace", "-f", str(candidate))
    updated = json.loads(run("kubectl", "--context", CONTEXT, "-n", NAMESPACE,
                             "get", f"configmap/{NAME}", "-o", "json"))
    if json.loads(updated["data"][KEY]) != candidate_dashboard or any(
        updated["data"].get(key) != value for key, value in live["data"].items() if key != KEY
    ):
        raise RuntimeError("Post-update dashboard data differs; inspect saved backup")
    print(f"PASS: updated only the lab dashboard; backup: {backup}")
    print("Grafana should load the new panel within 30 seconds; no restart required")


if __name__ == "__main__":
    main()
