"""Check an explicitly selected trusted candidate archive, then exercise only loopback fixtures."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import socket
import stat
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
import zipfile

MAX_ARCHIVE_BYTES = 256 << 20


def unpack(archive: Path, destination: Path, expected_sha256: str) -> dict:
    if not re.fullmatch(r"[0-9a-f]{64}", expected_sha256):
        raise ValueError("expected SHA-256 must be 64 lowercase hex characters")
    if archive.stat().st_size > MAX_ARCHIVE_BYTES:
        raise ValueError("archive too large")
    if hashlib.sha256(archive.read_bytes()).hexdigest() != expected_sha256:
        raise ValueError("archive checksum mismatch")
    with zipfile.ZipFile(archive) as bundle:
        entries = bundle.infolist()
        names = [entry.filename for entry in entries]
        if len(names) != len({name.casefold() for name in names}) or len(names) > 1000:
            raise ValueError("duplicate or excessive archive entries")
        if sum(entry.file_size for entry in entries) > MAX_ARCHIVE_BYTES:
            raise ValueError("expanded archive too large")
        for entry in entries:
            path = PurePosixPath(entry.filename)
            if (not path.parts or path.is_absolute() or ".." in path.parts or
                    path.as_posix() != entry.filename or "\\" in entry.filename or
                    any(part.endswith((".", " ")) or re.fullmatch(r"(?i)(con|prn|aux|nul|com[1-9]|lpt[1-9])(\..*)?", part) for part in path.parts) or
                    ":" in entry.filename or entry.is_dir() or
                    stat.S_IFMT(entry.external_attr >> 16) not in (0, stat.S_IFREG)):
                raise ValueError("unsafe archive entry")
        if "manifest.json" not in names or bundle.getinfo("manifest.json").file_size > 1 << 20:
            raise ValueError("missing or oversized manifest")
        manifest = json.loads(bundle.read("manifest.json"))
        if manifest.get("schema") != "forgeops.console.candidate/v1alpha1" or manifest.get("status") != "unsigned-candidate":
            raise ValueError("unsupported candidate manifest")
        if not re.fullmatch(r"[0-9a-f]{40}", manifest.get("commit", "")):
            raise ValueError("invalid source commit")
        files = manifest.get("files", {})
        if not isinstance(files, dict) or set(files) != set(names) - {"manifest.json"}:
            raise ValueError("manifest file set mismatch")
        extension = ".exe" if manifest.get("os") == "windows" else ""
        required = {"forgeops-console" + extension, "forgeops-console-demo" + extension,
                    "web/index.html", "web/forgeops-bundle.json", "README.md", "LICENSE"}
        if not required <= set(files):
            raise ValueError("candidate runtime files missing")
        # Validate every byte before extracting or executing anything.
        for name, expected in files.items():
            if hashlib.sha256(bundle.read(name)).hexdigest() != expected:
                raise ValueError("candidate member checksum mismatch")
        if json.loads(bundle.read("web/forgeops-bundle.json")) != manifest.get("bundle"):
            raise ValueError("manifest and browser identity differ")
        destination.mkdir(parents=True, exist_ok=False)
        for entry in entries:
            target = destination / entry.filename
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(bundle.read(entry))
            target.chmod(0o755 if entry.filename in required and entry.filename.startswith("forgeops-console") else 0o644)
        return manifest


def free_port() -> int:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return listener.getsockname()[1]


def exercise(package: Path, manifest: dict, working: Path, production: bool = False) -> None:
    extension = ".exe" if manifest["os"] == "windows" else ""
    binary = package / (("forgeops-console" if production else "forgeops-console-demo") + extension)
    address = f"127.0.0.1:{free_port()}"
    command = [str(binary), "--web-dir", str(package / "web"), "--listen", address]
    if production:
        # Never activate this context. Its token is a disclosure canary, not a credential.
        fixture = working / "synthetic-config.yaml"
        fixture.write_text('''apiVersion: v1
kind: Config
clusters:
- name: synthetic
  cluster:
    server: https://127.0.0.1:1
users:
- name: synthetic
  user:
    token: C7-SYNTHETIC-TOKEN-DO-NOT-DISCLOSE
contexts:
- name: synthetic
  context:
    cluster: synthetic
    user: synthetic
''', encoding="utf-8")
        command += ["--kubeconfig", str(fixture)]
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    process = subprocess.Popen(command, cwd=working, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    nonce = ""

    def request(path: str, body: dict | None = None, headers: dict | None = None) -> bytes:
        req = urllib.request.Request(f"http://{address}{path}",
            data=None if body is None else json.dumps(body).encode(),
            headers=headers if headers is not None else {"Content-Type": "application/json", "X-ForgeOps-Session": nonce})
        with opener.open(req, timeout=3) as response:
            assert response.headers.get("Cache-Control") == "no-store"
            assert "frame-ancestors 'none'" in response.headers.get("Content-Security-Policy", "")
            return response.read()

    try:
        deadline = time.monotonic() + 15
        while True:
            if process.poll() is not None:
                raise ValueError("installed candidate exited before bootstrap")
            try:
                raw = request("/api/v1/bootstrap")
                break
            except (urllib.error.URLError, TimeoutError):
                if time.monotonic() > deadline:
                    raise ValueError("installed candidate startup timed out") from None
                time.sleep(0.05)
        assert b"C7-SYNTHETIC-TOKEN-DO-NOT-DISCLOSE" not in raw
        bootstrap = json.loads(raw)
        assert bootstrap["bundle"] == manifest["bundle"]
        assert bootstrap["mode"] == ("read-only-c4" if production else "synthetic-demo")
        assert {p["id"] for p in bootstrap["plugins"]} == {"forge.example", "forge.resources", "forge.diagnostics"}
        assert not bootstrap["scope"]["context"]
        nonce = bootstrap["sessionNonce"]
        assert b"<html" in request("/")
        for headers, body, path in [({"Host": "foreign.invalid"}, None, "/api/v1/bootstrap"),
                                    ({"Origin": "https://foreign.invalid"}, None, "/api/v1/bootstrap"),
                                    ({"Content-Type": "application/json"}, {}, "/api/v1/activity")]:
            try:
                request(path, body, headers)
                raise AssertionError("installed boundary accepted denied request")
            except urllib.error.HTTPError as error:
                assert error.code == 403
        if not production:
            scope = json.loads(request("/api/v1/context", {"context": "synthetic-demo"}))
            namespaces = json.loads(request("/api/v1/plugins/forge.resources/query", {"generation": scope["generation"], "operation": "list", "resource": "namespaces"}))
            assert any(item["name"] == "signalforge" for item in namespaces["items"])
            scope = json.loads(request("/api/v1/namespace", {"generation": scope["generation"], "namespace": "signalforge"}))
            result = json.loads(request("/api/v1/plugins/forge.resources/query", {"generation": scope["generation"], "operation": "list", "resource": "pods"}))
            assert result["items"] and result["scope"] == scope
    finally:
        if process.poll() is None:
            process.terminate()
        try:
            process.communicate(timeout=7)
        except subprocess.TimeoutExpired:
            process.kill()
            process.communicate()
            raise ValueError("installed candidate did not stop within seven seconds") from None
    if os.name != "nt":
        assert process.returncode == 0, "Linux graceful shutdown failed"
    # Windows terminate() is forced cleanup, not evidence of Ctrl+C handling.


def verify(archive: Path, expected: str) -> None:
    with tempfile.TemporaryDirectory(prefix="console-installed-") as temporary:
        root = Path(temporary)
        package = root / "installed"
        manifest = unpack(archive, package, expected)
        native = "windows" if os.name == "nt" else "linux"
        if manifest["os"] != native or manifest["arch"] != "amd64":
            raise ValueError("candidate target does not match this verifier host")
        working = root / "unrelated-working-directory"
        working.mkdir()
        extension = ".exe" if native == "windows" else ""
        for name in ("forgeops-console", "forgeops-console-demo"):
            binary = package / (name + extension)
            info = json.loads(subprocess.check_output([str(binary), "--build-info"], cwd=working, timeout=10))
            assert info["commit"] == manifest["commit"] and info["bundle"] == manifest["bundle"]
            assert info["os"] == native and info["arch"] == manifest["arch"]
        denied = subprocess.run([str(package / ("forgeops-console" + extension)), "--web-dir", str(package / "web")],
                                cwd=working, capture_output=True, timeout=10)
        assert denied.returncode != 0 and b"explicit kubeconfig path is required" in denied.stderr
        exercise(package, manifest, working)
        exercise(package, manifest, working, production=True)
        # Preserve a whole valid pair, reject a damaged candidate, then restore it.
        previous = root / "previous-pair"
        shutil.copytree(package, previous)
        identity = package / "web/forgeops-bundle.json"
        bad = dict(manifest["bundle"], sourceDigest="0" * 64)
        identity.write_text(json.dumps(bad), encoding="utf-8")
        rejected = subprocess.run([str(package / ("forgeops-console-demo" + extension)), "--web-dir", str(package / "web")],
                                  cwd=working, capture_output=True, timeout=10)
        assert rejected.returncode != 0 and b"incompatible browser bundle" in rejected.stderr
        shutil.rmtree(package)
        shutil.copytree(previous, package)
        exercise(package, manifest, working)
    print("PASS: archive integrity, installed identity, loopback/nonce boundaries, synthetic reads, production offline bootstrap, mismatched pair rejection and restoration")
    if os.name == "nt":
        print("LIMIT: Windows process cleanup was forced; operator Ctrl+C acceptance remains required")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--sha256", required=True)
    args = parser.parse_args()
    verify(args.archive.resolve(), args.sha256)
