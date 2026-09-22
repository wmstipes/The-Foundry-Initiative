"""Build an unsigned native Console candidate from committed inputs, never local credentials."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
APP = "apps/forgeops-console"


def run(args: list[str], cwd: Path, env: dict[str, str] | None = None) -> str:
    return subprocess.check_output(args, cwd=cwd, env=env, text=True).strip()


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stage_source(root: Path, staged: Path, commit: str) -> None:
    # Read Git objects, not working-tree outputs, ignored files or kubeconfig.
    paths = run(["git", "ls-tree", "-r", "--name-only", commit, "--", APP, "LICENSE",
                 "docs/releases/forgeops-console-candidate.md"], root).splitlines()
    for name in paths:
        mode = run(["git", "ls-tree", commit, "--", name], root).split()[0]
        if mode not in ("100644", "100755"):
            raise ValueError(f"non-regular source input: {name}")
        target = staged / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(subprocess.check_output(["git", "show", f"{commit}:{name}"], cwd=root))


def collect_notices(app: Path, package: Path, go: str, env: dict[str, str]) -> None:
    notices = package / "notices"
    notices.mkdir()
    modules = run([go, "list", "-deps", "-f", "{{if .Module}}{{.Module.Path}}|{{.Module.Dir}}{{end}}", "./cmd/..."], app, env)
    dependencies = sorted({line for line in modules.splitlines() if "|" in line and not line.startswith("github.com/wmstipes/The-Foundry-Initiative/")})
    for index, line in enumerate(dependencies):
        name, directory = line.split("|", 1)
        if not directory:
            raise ValueError(f"module not downloaded: {name}")
        sources = [p for p in Path(directory).iterdir()
                   if p.is_file() and p.name.upper().startswith(("LICENSE", "COPYING", "NOTICE"))]
        if not sources:
            raise ValueError(f"license notice missing: {name}")
        destination = notices / f"go-{index:03}"
        destination.mkdir()
        (destination / "MODULE.txt").write_text(name + "\n", encoding="utf-8")
        for source in sources:
            shutil.copyfile(source, destination / source.name)
    for name in ("react", "react-dom", "scheduler"):
        destination = notices / name
        destination.mkdir()
        shutil.copyfile(app / "web/node_modules" / name / "LICENSE", destination / "LICENSE")
    goroot = Path(run([go, "env", "GOROOT"], app, env))
    shutil.copyfile(goroot / "LICENSE", notices / "GO-LICENSE")


def build(output: Path, go: str) -> Path:
    commit = run(["git", "rev-parse", "HEAD"], ROOT)
    tree = run(["git", "rev-parse", "HEAD^{tree}"], ROOT)
    if run(["git", "status", "--porcelain", "--untracked-files=no"], ROOT):
        raise ValueError("commit tracked changes before building a candidate")
    env = os.environ.copy()
    env.update({"CGO_ENABLED": "0", "GOWORK": "off", "GOFLAGS": ""})
    # Candidates are native; inherited cross-compilation settings are not admitted.
    env.pop("GOOS", None)
    env.pop("GOARCH", None)
    target = json.loads(run([go, "env", "-json", "GOOS", "GOARCH"], ROOT, env))
    if (target["GOOS"], target["GOARCH"]) not in (("linux", "amd64"), ("windows", "amd64")):
        raise ValueError("candidate targets are linux/amd64 and windows/amd64 only")
    output.mkdir(parents=True, exist_ok=False)
    npm = shutil.which("npm.cmd" if os.name == "nt" else "npm")
    if npm is None:
        raise ValueError("npm is required")
    with tempfile.TemporaryDirectory(prefix="console-candidate-") as temporary:
        staging = Path(temporary)
        source = staging / "source"
        stage_source(ROOT, source, commit)
        app = source / APP
        subprocess.run([npm, "ci"], cwd=app / "web", env=env, check=True)
        subprocess.run([npm, "run", "build"], cwd=app / "web", env=env, check=True)
        locked = {name: (app / name).read_bytes() for name in ("go.mod", "go.sum")}
        subprocess.run([go, "mod", "download"], cwd=app, env=env, check=True)
        package = staging / "package"
        package.mkdir()
        extension = ".exe" if target["GOOS"] == "windows" else ""
        module = "github.com/wmstipes/The-Foundry-Initiative/apps/forgeops-console"
        for entry in ("forgeops-console", "forgeops-console-demo"):
            subprocess.run([go, "build", "-trimpath", "-buildvcs=false", "-mod=readonly",
                            "-ldflags", f"-X {module}.BuildCommit={commit}",
                            "-o", str(package / (entry + extension)), f"./cmd/{entry}"],
                           cwd=app, env=env, check=True)
        if any((app / name).read_bytes() != data for name, data in locked.items()):
            raise ValueError("candidate build changed the locked Go module graph")
        shutil.copytree(app / "web/dist", package / "web")
        shutil.copyfile(source / "LICENSE", package / "LICENSE")
        shutil.copyfile(source / "docs/releases/forgeops-console-candidate.md", package / "README.md")
        collect_notices(app, package, go, env)
        (package / "go-modules.txt").write_text(
            "\n".join(sorted(set(run([go, "list", "-deps", "-f", "{{if .Module}}{{.Module.Path}} {{.Module.Version}}{{end}}", "./cmd/..."], app, env).splitlines()) - {""})) + "\n", encoding="utf-8")
        shutil.copyfile(app / "web/package-lock.json", package / "browser-package-lock.json")
        files = {p.relative_to(package).as_posix(): digest(p)
                 for p in sorted(package.rglob("*")) if p.is_file()}
        manifest = {"schema": "forgeops.console.candidate/v1alpha1", "status": "unsigned-candidate",
                    "commit": commit, "tree": tree, "os": target["GOOS"], "arch": target["GOARCH"],
                    "go": run([go, "version"], app, env), "node": run(["node", "--version"], app),
                    "npm": run([npm, "--version"], app),
                    "bundle": json.loads((package / "web/forgeops-bundle.json").read_text()), "files": files}
        (package / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        archive = output / f"forgeops-console-candidate-{commit[:12]}-{target['GOOS']}-{target['GOARCH']}.zip"
        with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
            for path in sorted(package.rglob("*")):
                if path.is_file():
                    info = zipfile.ZipInfo(path.relative_to(package).as_posix(), (1980, 1, 1, 0, 0, 0))
                    info.compress_type = zipfile.ZIP_DEFLATED
                    info.create_system = 3
                    info.external_attr = (0o100755 if path.name.startswith("forgeops-console") else 0o100644) << 16
                    bundle.writestr(info, path.read_bytes())
        (output / "SHA256SUMS.txt").write_text(f"{digest(archive)}  {archive.name}\n", encoding="utf-8")
        return archive


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--go", default="go")
    args = parser.parse_args()
    print(build(args.output_dir.resolve(), args.go))
