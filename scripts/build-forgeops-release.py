"""Build and checksum the exact ForgeOps wheel candidate."""

from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import tomllib


SOURCE_DATE_EPOCH = "315532800"  # 1980-01-01, the earliest portable ZIP date.


def project_version(root: Path) -> str:
    with (root / "pyproject.toml").open("rb") as stream:
        project = tomllib.load(stream)["project"]
    if project["name"] != "signalforge-forgeops":
        raise ValueError("unexpected project name")
    return project["version"]


def stage_source(root: Path, staged: Path) -> None:
    staged.mkdir()
    for filename in ("pyproject.toml", "README.md", "LICENSE"):
        shutil.copy2(root / filename, staged / filename)
    shutil.copytree(root / "src" / "forgeops", staged / "src" / "forgeops")


def build(root: Path, output: Path) -> Path:
    version = project_version(root)
    expected = output / f"signalforge_forgeops-{version}-py3-none-any.whl"
    output.mkdir(parents=True, exist_ok=False)
    environment = os.environ.copy()
    environment["SOURCE_DATE_EPOCH"] = SOURCE_DATE_EPOCH
    with tempfile.TemporaryDirectory(prefix="forgeops-release-") as temporary:
        staged = Path(temporary) / "source"
        stage_source(root, staged)
        subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "wheel",
                ".",
                "--no-deps",
                "--no-build-isolation",
                "--wheel-dir",
                str(output),
            ],
            cwd=staged,
            env=environment,
            check=True,
        )
    wheels = sorted(output.glob("*.whl"))
    if wheels != [expected]:
        raise ValueError("build did not produce exactly the expected wheel")
    digest = hashlib.sha256(expected.read_bytes()).hexdigest()
    (output / "SHA256SUMS.txt").write_text(
        f"{digest}  {expected.name}\n", encoding="utf-8", newline="\n",
    )
    return expected


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    try:
        wheel = build(root, Path(args.output_dir).resolve())
    except (OSError, subprocess.CalledProcessError, ValueError) as exc:
        print(f"ForgeOps release build failed: {exc}", file=sys.stderr)
        return 2
    print(wheel)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
