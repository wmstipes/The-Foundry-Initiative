"""Read-only publication preflight; never creates tags, releases, or images."""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import time
import urllib.error
import urllib.request


REPOSITORY = "wmstipes/The-Foundry-Initiative"


def validate_context(env: dict[str, str], checkout_sha: str) -> str:
    sha = env.get("GITHUB_SHA", "")
    if env.get("GITHUB_REPOSITORY") != REPOSITORY:
        raise ValueError("Publication is restricted to the canonical repository")
    if not re.fullmatch(r"[0-9a-f]{40}", sha) or checkout_sha != sha:
        raise ValueError("Checkout must match the full workflow source SHA")
    event, ref = env.get("GITHUB_EVENT_NAME"), env.get("GITHUB_REF", "")
    if event == "workflow_dispatch":
        if ref != "refs/heads/main" or env.get("EXPECTED_SOURCE_SHA") != sha:
            raise ValueError("Manual publication requires main and its reviewed source SHA")
    elif event == "push":
        if ref != "refs/heads/main" and not re.fullmatch(
            r"refs/tags/(?:forgeops-v|forge-yaml-workbench-v|v)\d+\.\d+\.\d+", ref
        ):
            raise ValueError("Push publication requires main or an approved release tag")
    else:
        raise ValueError("This event cannot publish")
    return sha


def gh_get(endpoint: str) -> dict:
    result = subprocess.run(
        ["gh", "api", "--method", "GET", endpoint], check=True,
        capture_output=True, text=True, timeout=30,
    )
    return json.loads(result.stdout)


def validated_main_source(sha: str, get=gh_get) -> bool:
    endpoint = (
        f"repos/{REPOSITORY}/actions/workflows/required-validation.yml/runs"
        f"?head_sha={sha}&branch=main&event=push&per_page=100"
    )
    runs = get(endpoint)["workflow_runs"]
    # The newest run/attempt must succeed: an old green run cannot hide a red rerun.
    candidates = [r for r in runs if r.get("head_sha") == sha
                  and r.get("head_branch") == "main" and r.get("event") == "push"
                  and r.get("path") == ".github/workflows/required-validation.yml"
                  and r.get("repository", {}).get("full_name") == REPOSITORY]
    if not candidates:
        return False
    run = max(candidates, key=lambda r: r["id"])
    if run.get("status") != "completed" or run.get("conclusion") != "success":
        return False
    jobs = get(f"repos/{REPOSITORY}/actions/runs/{run['id']}/jobs?filter=latest&per_page=100")
    if jobs["total_count"] > len(jobs["jobs"]):
        raise ValueError("Job list incomplete; refusing publication")
    gates = [j for j in jobs["jobs"] if j["name"] == "Gate 4 required validation"]
    return len(gates) == 1 and gates[0].get("conclusion") == "success"


def require_unused_image(image: str, version: str) -> None:
    if not re.fullmatch(r"wmstipes/[a-z0-9-]+", image):
        raise ValueError("Unexpected image repository")
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        raise ValueError("Image version must be MAJOR.MINOR.PATCH")
    url = f"https://hub.docker.com/v2/repositories/{image}/tags/{version}"
    try:
        with urllib.request.urlopen(url, timeout=20):
            pass
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return
        raise ValueError(f"Cannot verify image absence: HTTP {error.code}") from error
    raise ValueError("Versioned image already exists; choose a new version")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image")
    parser.add_argument("--version")
    parser.add_argument("--wait-seconds", type=int, default=600)
    args = parser.parse_args()
    try:
        if bool(args.image) != bool(args.version):
            raise ValueError("Image and version must be supplied together")
        if not 0 <= args.wait_seconds <= 600:
            raise ValueError("Wait must be between zero and 600 seconds")
        checkout = subprocess.run(["git", "rev-parse", "HEAD"], check=True,
                                  capture_output=True, text=True, timeout=10).stdout.strip()
        sha = validate_context(dict(os.environ), checkout)
        deadline = time.monotonic() + args.wait_seconds
        while not validated_main_source(sha):
            if time.monotonic() >= deadline:
                raise ValueError("Exact source has no successful main-push validation")
            print("Waiting for exact main-source validation...", flush=True)
            time.sleep(min(15, max(0, deadline - time.monotonic())))
        if args.image:
            require_unused_image(args.image, args.version)
        print(f"PASS: publication source {sha} validated on main")
        return 0
    except (ValueError, KeyError, OSError, subprocess.SubprocessError) as error:
        # Do not print captured API responses, headers, or credentials.
        print(f"Publication preflight failed: {type(error).__name__}: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
