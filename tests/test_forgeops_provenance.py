from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from forgeops.cli import build_parser, main  # noqa: E402
from forgeops.provenance import (  # noqa: E402
    DISTRIBUTION_NAME,
    ExecutionProvenance,
    inspect_execution_provenance,
    render_execution_provenance,
)


class FakeDistribution:
    def __init__(self, version: str, direct_url: dict[str, object] | None = None):
        self.version = version
        self._direct_url = direct_url

    def read_text(self, filename: str) -> str | None:
        if filename != "direct_url.json" or self._direct_url is None:
            return None
        return json.dumps(self._direct_url)


class ForgeOpsProvenanceTests(unittest.TestCase):
    def test_command_is_explicitly_supported(self) -> None:
        args = build_parser().parse_args(["provenance"])
        self.assertEqual("provenance", args.command)

    def test_normal_install_reports_matching_identity(self) -> None:
        with mock.patch(
            "forgeops.provenance.metadata.distribution",
            return_value=FakeDistribution("0.9.0"),
        ):
            result = inspect_execution_provenance(
                module_path=Path("/installed/forgeops/provenance.py"),
                module_version="0.9.0",
                environ={},
                python_executable="/venv/python",
            )
        self.assertEqual(DISTRIBUTION_NAME, result.distribution_name)
        self.assertEqual("0.9.0", result.distribution_version)
        self.assertIsNone(result.source_project_version)
        self.assertEqual("installed", result.execution_mode)
        self.assertEqual("/venv/python", result.python_executable)
        self.assertEqual("OK", result.status)
        self.assertEqual(0, result.exit_code)

    def test_version_mismatch_is_an_error(self) -> None:
        with mock.patch(
            "forgeops.provenance.metadata.distribution",
            return_value=FakeDistribution("0.6.0"),
        ):
            result = inspect_execution_provenance(
                module_path=Path("/installed/forgeops/provenance.py"),
                module_version="0.9.0",
                environ={},
            )
        self.assertEqual("ERROR", result.status)
        self.assertEqual(2, result.exit_code)
        self.assertIn("does not match", result.findings[0])

    def test_temporary_editable_install_is_visible_and_warns(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory)
            module = source / "src" / "forgeops" / "provenance.py"
            module.parent.mkdir(parents=True)
            module.write_text("fixture", encoding="utf-8")
            direct_url = {
                "url": source.as_uri(),
                "dir_info": {"editable": True},
            }
            with mock.patch(
                "forgeops.provenance.metadata.distribution",
                return_value=FakeDistribution("0.9.0", direct_url),
            ):
                result = inspect_execution_provenance(
                    module_path=module,
                    module_version="0.9.0",
                    environ={},
                )
        self.assertEqual("editable", result.execution_mode)
        self.assertEqual("WARN", result.status)
        self.assertEqual(1, result.exit_code)
        self.assertIn("temporary directory", result.findings[0])

    def test_missing_editable_source_is_an_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            missing_source = Path(directory) / "deleted-worktree"
            direct_url = {
                "url": missing_source.as_uri(),
                "dir_info": {"editable": True},
            }
        with mock.patch(
            "forgeops.provenance.metadata.distribution",
            return_value=FakeDistribution("0.9.0", direct_url),
        ):
            result = inspect_execution_provenance(
                module_path=Path("/installed/forgeops/provenance.py"),
                module_version="0.9.0",
                environ={},
            )
        self.assertEqual("ERROR", result.status)
        self.assertIn("no longer exists", result.findings[0])

    def test_non_file_install_source_redacts_credentials_and_query(self) -> None:
        direct_url = {
            "url": "https://user:secret@example.test/repository?token=value#commit",
        }
        with mock.patch(
            "forgeops.provenance.metadata.distribution",
            return_value=FakeDistribution("0.9.0", direct_url),
        ):
            result = inspect_execution_provenance(
                module_path=Path("/installed/forgeops/provenance.py"),
                module_version="0.9.0",
                environ={},
            )
        self.assertEqual("https://example.test/repository", result.install_source)
        self.assertNotIn("secret", result.install_source or "")
        self.assertNotIn("token", result.install_source or "")

    def test_declared_source_mode_checks_current_tree(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            module = root / "src" / "forgeops" / "provenance.py"
            module.parent.mkdir(parents=True)
            module.write_text("fixture", encoding="utf-8")
            (root / "pyproject.toml").write_text(
                '[project]\nname = "foundry-check"\nversion = "0.9.0"\n',
                encoding="utf-8",
            )
            result = inspect_execution_provenance(
                module_path=module,
                module_version="0.9.0",
                environ={"FORGEOPS_SOURCE_ROOT": str(root)},
                python_executable="python",
            )
        self.assertEqual("source", result.execution_mode)
        self.assertIsNone(result.distribution_version)
        self.assertEqual("0.9.0", result.source_project_version)
        self.assertEqual("OK", result.status)
        self.assertEqual(0, result.exit_code)

    def test_declared_source_version_mismatch_is_an_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            module = root / "src" / "forgeops" / "provenance.py"
            module.parent.mkdir(parents=True)
            module.write_text("fixture", encoding="utf-8")
            (root / "pyproject.toml").write_text(
                '[project]\nname = "foundry-check"\nversion = "0.6.0"\n',
                encoding="utf-8",
            )
            result = inspect_execution_provenance(
                module_path=module,
                module_version="0.9.0",
                environ={"FORGEOPS_SOURCE_ROOT": str(root)},
            )
        self.assertEqual("ERROR", result.status)
        self.assertIn("source project version", result.findings[0])

    def test_renderer_includes_identity_and_findings(self) -> None:
        provenance = ExecutionProvenance(
            distribution_name="foundry-check",
            distribution_version="0.9.0",
            source_project_version=None,
            module_version="0.9.0",
            module_path="C:\\repo\\src\\forgeops\\provenance.py",
            python_executable="C:\\repo\\.venv\\Scripts\\python.exe",
            execution_mode="source",
            install_source="C:\\repo",
            status="WARN",
            findings=("review this installation",),
        )
        output = StringIO()
        render_execution_provenance(provenance, output)
        rendered = output.getvalue()
        self.assertIn("status: WARN", rendered)
        self.assertIn("moduleVersion: 0.9.0", rendered)
        self.assertIn("sourceProjectVersion: unavailable", rendered)
        self.assertIn("executionMode: source", rendered)
        self.assertIn("- review this installation", rendered)

    def test_cli_renders_provenance_without_collection(self) -> None:
        provenance = ExecutionProvenance(
            distribution_name="foundry-check",
            distribution_version="0.9.0",
            source_project_version=None,
            module_version="0.9.0",
            module_path="module",
            python_executable="python",
            execution_mode="installed",
            install_source=None,
            status="OK",
            findings=(),
        )
        output = StringIO()
        with mock.patch(
            "forgeops.cli.inspect_execution_provenance", return_value=provenance,
        ), mock.patch("forgeops.cli.KubectlRunner") as kubectl, \
                mock.patch("forgeops.cli.Collector") as collector, \
                mock.patch("forgeops.cli.HttpRunner") as http, \
                redirect_stdout(output):
            exit_code = main(["provenance"])
        self.assertEqual(0, exit_code)
        self.assertIn("ForgeOps execution provenance", output.getvalue())
        kubectl.assert_not_called()
        collector.assert_not_called()
        http.assert_not_called()

    def test_source_launcher_selects_repository_checkout(self) -> None:
        repository = Path(__file__).resolve().parents[1]
        launcher = repository / "scripts" / "run-forgeops-dev.py"
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [sys.executable, str(launcher), "provenance"],
                cwd=directory,
                check=False,
                capture_output=True,
                text=True,
                timeout=10,
            )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("status: OK", result.stdout)
        self.assertIn("executionMode: source", result.stdout)
        self.assertIn(
            f"modulePath: {repository / 'src' / 'forgeops' / 'provenance.py'}",
            result.stdout,
        )


if __name__ == "__main__":
    unittest.main()
