"""Rehearse a matched Console demo, rejected mismatch, and restored pair offline.

Requires a freshly built synthetic-demo executable and browser directory.
Uses only Python's standard library and literal loopback HTTP. Never loads
kubeconfig or launches the production executable's cluster workflow.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import socket
import subprocess
import tempfile
import time
import urllib.error
import urllib.request


def port() -> int:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


def matched(binary: Path, assets: Path) -> None:
    expected = json.loads((assets / "forgeops-bundle.json").read_text())
    address = f"127.0.0.1:{port()}"
    process = subprocess.Popen(
        [str(binary), "--web-dir", str(assets), "--listen", address],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    nonce = ""

    def request(path: str, body: dict | None = None) -> dict:
        data = None if body is None else json.dumps(body).encode()
        req = urllib.request.Request(
            f"http://{address}{path}", data=data,
            headers={"Content-Type": "application/json", "X-ForgeOps-Session": nonce},
        )
        with opener.open(req, timeout=2) as response:
            assert response.headers.get("Cache-Control") == "no-store"
            return json.load(response)

    try:
        deadline = time.monotonic() + 10
        while True:
            if process.poll() is not None:
                raise AssertionError("matched demo exited before bootstrap")
            try:
                bootstrap = request("/api/v1/bootstrap")
                break
            except (urllib.error.URLError, TimeoutError):
                if time.monotonic() >= deadline:
                    raise AssertionError("matched demo did not start") from None
                time.sleep(0.05)
        assert bootstrap["mode"] == "synthetic-demo", "only the synthetic demo is permitted"
        assert bootstrap["bundle"] == expected, "Go and Vite fingerprints differ"
        assert {p["id"] for p in bootstrap["plugins"]} == {"forge.example", "forge.resources", "forge.diagnostics"}
        nonce = bootstrap["sessionNonce"]
        scope = request("/api/v1/context", {"context": "synthetic-demo"})
        namespaces = request("/api/v1/plugins/forge.resources/query", {"generation": scope["generation"], "operation": "list", "resource": "namespaces"})
        assert any(item["name"] == "signalforge" for item in namespaces["items"])
        scope = request("/api/v1/namespace", {"generation": scope["generation"], "namespace": "signalforge"})
        pods = request("/api/v1/plugins/forge.resources/query", {"generation": scope["generation"], "operation": "list", "resource": "pods"})
        assert pods["scope"] == scope and pods["items"]
    finally:
        if process.poll() is None:
            process.terminate()
        try:
            _, stderr = process.communicate(timeout=7)
        except subprocess.TimeoutExpired:
            process.kill()
            process.communicate()
            raise AssertionError("demo shutdown exceeded bound") from None
    assert process.returncode == 0, f"demo shutdown failed: {stderr}"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--web-dir", type=Path, required=True)
    args = parser.parse_args()
    binary, assets = args.binary.resolve(), args.web_dir.resolve()
    matched(binary, assets)
    with tempfile.TemporaryDirectory(prefix="console-bundle-") as directory:
        mismatched = Path(directory) / "web"
        shutil.copytree(assets, mismatched)
        identity = json.loads((mismatched / "forgeops-bundle.json").read_text())
        identity["sourceDigest"] = "0" * 64
        (mismatched / "forgeops-bundle.json").write_text(json.dumps(identity))
        rejected = subprocess.run(
            [str(binary), "--web-dir", str(mismatched), "--listen", f"127.0.0.1:{port()}"],
            capture_output=True, text=True, timeout=10,
        )
        assert rejected.returncode != 0 and "incompatible browser bundle" in rejected.stderr
    matched(binary, assets)
    print("PASS: matched synthetic pair, mismatched startup rejection, restored pair, bounded shutdown")


if __name__ == "__main__":
    main()
