"""Validate a bounded ForgeOps wheel and its exact SHA-256 record."""

from __future__ import annotations

import argparse
from email.parser import Parser
import hashlib
from pathlib import Path
import sys
import tomllib
from zipfile import BadZipFile, ZipFile


PROJECT_NAME = "signalforge-forgeops"
PYTHON_RANGE = "<3.15,>=3.11"
ENTRY_POINTS = "[console_scripts]\nforgeops = forgeops.cli:main\n"
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def expected_version(root: Path) -> str:
    with (root / "pyproject.toml").open("rb") as stream:
        project = tomllib.load(stream)["project"]
    if project["name"] != PROJECT_NAME:
        raise ValueError("unexpected project name")
    return project["version"]


def validate(directory: Path, version: str) -> tuple[Path, str]:
    wheel_name = f"signalforge_forgeops-{version}-py3-none-any.whl"
    wheel = directory / wheel_name
    checksum = directory / "SHA256SUMS.txt"
    if sorted(path.name for path in directory.iterdir()) != [
        "SHA256SUMS.txt", wheel_name,
    ]:
        raise ValueError("release directory must contain only the wheel and checksum")
    digest = hashlib.sha256(wheel.read_bytes()).hexdigest()
    if checksum.read_text(encoding="utf-8") != f"{digest}  {wheel_name}\n":
        raise ValueError("checksum record does not exactly match the wheel")

    dist_info = f"signalforge_forgeops-{version}.dist-info"
    with ZipFile(wheel) as archive:
        names = archive.namelist()
        package_names = {
            path.relative_to(REPOSITORY_ROOT / "src").as_posix()
            for path in (REPOSITORY_ROOT / "src" / "forgeops").rglob("*.py")
        }
        expected_names = package_names | {
            f"{dist_info}/METADATA",
            f"{dist_info}/WHEEL",
            f"{dist_info}/entry_points.txt",
            f"{dist_info}/licenses/LICENSE",
            f"{dist_info}/top_level.txt",
            f"{dist_info}/RECORD",
        }
        if len(names) != len(set(names)) or set(names) != expected_names:
            raise ValueError("wheel file manifest does not exactly match ForgeOps")
        metadata = Parser().parsestr(
            archive.read(f"{dist_info}/METADATA").decode("utf-8"),
        )
        if metadata["Name"] != PROJECT_NAME:
            raise ValueError("wheel project name is incorrect")
        if metadata["Version"] != version:
            raise ValueError("wheel version is incorrect")
        if metadata["Requires-Python"] != PYTHON_RANGE:
            raise ValueError("wheel Python range is incorrect")
        if metadata["License-Expression"] != "MIT":
            raise ValueError("wheel license expression is incorrect")
        if metadata.get_all("Requires-Dist", []) != []:
            raise ValueError("wheel unexpectedly declares runtime dependencies")
        if archive.read(f"{dist_info}/entry_points.txt").decode() != ENTRY_POINTS:
            raise ValueError("wheel entry point is incorrect")
        license_text = archive.read(f"{dist_info}/licenses/LICENSE").decode()
        if "MIT License" not in license_text or "Michael Stipes" not in license_text:
            raise ValueError("wheel MIT license text is incorrect")
    return wheel, digest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dist-dir", required=True)
    args = parser.parse_args()
    try:
        wheel, digest = validate(
            Path(args.dist_dir).resolve(), expected_version(REPOSITORY_ROOT),
        )
    except (BadZipFile, KeyError, OSError, UnicodeError, ValueError) as exc:
        print(f"ForgeOps release validation failed: {exc}", file=sys.stderr)
        return 2
    print(f"VALID {wheel.name} sha256={digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
