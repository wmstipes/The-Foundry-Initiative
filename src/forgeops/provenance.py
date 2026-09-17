"""Inspect and render the local ForgeOps execution identity."""

from __future__ import annotations

from dataclasses import dataclass
from importlib import metadata
import json
import os
from pathlib import Path
import sys
import tempfile
import tomllib
from typing import Mapping, TextIO
from urllib.parse import unquote, urlparse
from urllib.request import url2pathname

from . import __version__


DISTRIBUTION_NAME = "foundry-check"
SOURCE_MODE_ENV = "FORGEOPS_SOURCE_ROOT"


@dataclass(frozen=True)
class ExecutionProvenance:
    """Resolved local identity for one ForgeOps invocation."""

    distribution_name: str
    distribution_version: str | None
    source_project_version: str | None
    module_version: str
    module_path: str
    python_executable: str
    execution_mode: str
    install_source: str | None
    status: str
    findings: tuple[str, ...]

    @property
    def exit_code(self) -> int:
        if self.status == "ERROR":
            return 2
        if self.status == "WARN":
            return 1
        return 0


def _display_path(path: Path) -> str:
    return str(path.expanduser().resolve(strict=False))


def _file_url_path(url: str) -> Path | None:
    parsed = urlparse(url)
    if parsed.scheme != "file":
        return None
    path = url2pathname(unquote(parsed.path))
    if parsed.netloc:
        path = f"//{parsed.netloc}{path}"
    return Path(path)


def _safe_source_url(url: str) -> str:
    """Display a non-file source without credentials, query, or fragment."""

    parsed = urlparse(url)
    if not parsed.scheme:
        return "unrecognized source"
    host = parsed.hostname or ""
    if ":" in host and not host.startswith("["):
        host = f"[{host}]"
    try:
        port = parsed.port
    except ValueError:
        port = None
    if port is not None:
        host = f"{host}:{port}"
    prefix = f"{parsed.scheme}://{host}" if host else f"{parsed.scheme}:"
    return f"{prefix}{parsed.path}"


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.resolve(strict=False).relative_to(parent.resolve(strict=False))
    except ValueError:
        return False
    return True


def _project_version(root: Path) -> str | None:
    pyproject = root / "pyproject.toml"
    try:
        with pyproject.open("rb") as stream:
            value = tomllib.load(stream)["project"]["version"]
    except (OSError, KeyError, TypeError, tomllib.TOMLDecodeError):
        return None
    return value if isinstance(value, str) else None


def inspect_execution_provenance(
    *,
    module_path: Path | None = None,
    module_version: str = __version__,
    environ: Mapping[str, str] | None = None,
    python_executable: str | None = None,
) -> ExecutionProvenance:
    """Resolve execution identity without collection, network, or mutation."""

    environment = os.environ if environ is None else environ
    loaded_module = (
        Path(__file__).resolve(strict=False)
        if module_path is None
        else module_path.resolve(strict=False)
    )
    executable = Path(python_executable or sys.executable).expanduser().absolute()
    findings: list[str] = []
    errors: list[str] = []
    distribution_version: str | None = None
    source_project_version: str | None = None
    install_source: str | None = None
    execution_mode = "unknown"

    source_root_value = environment.get(SOURCE_MODE_ENV)
    if source_root_value:
        source_root = Path(source_root_value).expanduser().resolve(strict=False)
        install_source = _display_path(source_root)
        execution_mode = "source"
        expected_package = source_root / "src" / "forgeops"
        if not source_root.is_dir():
            errors.append("declared source root is not an accessible directory")
        elif not _is_within(loaded_module, expected_package):
            errors.append("loaded module is outside the declared source tree")
        source_project_version = _project_version(source_root)
        if source_project_version is None:
            errors.append("declared source root has no readable project version")
        elif source_project_version != module_version:
            errors.append(
                "source project version does not match the loaded module version"
            )
    else:
        try:
            distribution = metadata.distribution(DISTRIBUTION_NAME)
        except metadata.PackageNotFoundError:
            findings.append(
                "distribution metadata is unavailable; use the supported source launcher "
                "or install ForgeOps in an isolated environment"
            )
        else:
            distribution_version = distribution.version
            if distribution_version != module_version:
                errors.append(
                    "installed distribution version does not match the loaded module version"
                )
            try:
                direct_url_text = distribution.read_text("direct_url.json")
            except (OSError, UnicodeError):
                direct_url_text = None
                findings.append("installation source metadata is unreadable")
            if direct_url_text:
                try:
                    direct_url = json.loads(direct_url_text)
                except json.JSONDecodeError:
                    findings.append("installation source metadata is malformed")
                else:
                    if not isinstance(direct_url, dict):
                        findings.append("installation source metadata has an invalid shape")
                    else:
                        source_url = direct_url.get("url")
                        source_path = (
                            _file_url_path(source_url)
                            if isinstance(source_url, str)
                            else None
                        )
                        dir_info = direct_url.get("dir_info")
                        editable = (
                            isinstance(dir_info, dict)
                            and dir_info.get("editable") is True
                        )
                        if source_path is not None:
                            install_source = _display_path(source_path)
                        elif isinstance(source_url, str):
                            install_source = _safe_source_url(source_url)
                        if editable:
                            execution_mode = "editable"
                            if source_path is None:
                                findings.append(
                                    "editable installation source is not a local file path"
                                )
                            elif not source_path.is_dir():
                                errors.append(
                                    "editable installation source no longer exists"
                                )
                            else:
                                if not _is_within(loaded_module, source_path):
                                    errors.append(
                                        "loaded module is outside the editable installation source"
                                    )
                                temporary_root = Path(tempfile.gettempdir())
                                if _is_within(source_path, temporary_root):
                                    findings.append(
                                        "editable installation points into a temporary directory"
                                    )
                        else:
                            execution_mode = "local-install"
            else:
                execution_mode = "installed"

    combined_findings = tuple(errors + findings)
    status = "ERROR" if errors else "WARN" if findings else "OK"
    return ExecutionProvenance(
        distribution_name=DISTRIBUTION_NAME,
        distribution_version=distribution_version,
        source_project_version=source_project_version,
        module_version=module_version,
        module_path=_display_path(loaded_module),
        python_executable=str(executable),
        execution_mode=execution_mode,
        install_source=install_source,
        status=status,
        findings=combined_findings,
    )


def render_execution_provenance(
    provenance: ExecutionProvenance,
    stream: TextIO,
) -> None:
    """Render the identity as a stable, local operator report."""

    stream.write("ForgeOps execution provenance\n")
    stream.write(f"status: {provenance.status}\n")
    stream.write(f"distribution: {provenance.distribution_name}\n")
    stream.write(
        f"distributionVersion: {provenance.distribution_version or 'unavailable'}\n"
    )
    stream.write(
        f"sourceProjectVersion: {provenance.source_project_version or 'unavailable'}\n"
    )
    stream.write(f"moduleVersion: {provenance.module_version}\n")
    stream.write(f"executionMode: {provenance.execution_mode}\n")
    stream.write(f"modulePath: {provenance.module_path}\n")
    stream.write(f"pythonExecutable: {provenance.python_executable}\n")
    stream.write(f"installSource: {provenance.install_source or 'unavailable'}\n")
    if provenance.findings:
        stream.write("findings:\n")
        for finding in provenance.findings:
            stream.write(f"- {finding}\n")
