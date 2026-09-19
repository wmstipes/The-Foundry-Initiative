from __future__ import annotations

import importlib.util
from pathlib import Path
import re
import tempfile
import tomllib
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ForgeOpsReleaseCandidateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.package = tomllib.loads(
            (ROOT / "pyproject.toml").read_text(encoding="utf-8"),
        )

    def test_product_identity_and_version_are_explicit(self) -> None:
        project = self.package["project"]
        self.assertEqual("signalforge-forgeops", project["name"])
        self.assertEqual("1.0.0", project["version"])
        self.assertEqual({"forgeops": "forgeops.cli:main"}, project["scripts"])
        self.assertEqual([], project["dependencies"])

    def test_declared_python_range_matches_ci_matrix(self) -> None:
        self.assertEqual(">=3.11,<3.15", self.package["project"]["requires-python"])
        workflow = (ROOT / ".github/workflows/forgeops-ci.yml").read_text()
        for version in ("3.11", "3.12", "3.13", "3.14"):
            self.assertIn(f'"{version}"', workflow)

    def test_only_forgeops_is_selected_for_the_wheel(self) -> None:
        package_filter = self.package["tool"]["setuptools"]["packages"]["find"]
        self.assertEqual(["forgeops*"], package_filter["include"])

    def test_module_and_project_versions_match(self) -> None:
        module = (ROOT / "src/forgeops/__init__.py").read_text()
        match = re.search(r'__version__ = "([^"]+)"', module)
        self.assertIsNotNone(match)
        self.assertEqual(self.package["project"]["version"], match.group(1))

    def test_mit_license_is_declared_and_present(self) -> None:
        self.assertEqual("MIT", self.package["project"]["license"])
        self.assertEqual(["LICENSE"], self.package["project"]["license-files"])
        license_text = (ROOT / "LICENSE").read_text()
        self.assertIn("MIT License", license_text)
        self.assertIn("Copyright (c) 2026 Michael Stipes", license_text)

    def test_normal_ci_has_read_only_permissions(self) -> None:
        workflow = (ROOT / ".github/workflows/forgeops-ci.yml").read_text()
        self.assertIn("permissions:\n  contents: read", workflow)
        self.assertNotIn("contents: write", workflow)
        self.assertNotIn("gh release create", workflow)

    def test_release_workflow_is_tag_only_and_minimally_writable(self) -> None:
        workflow = (ROOT / ".github/workflows/forgeops-release.yml").read_text()
        self.assertIn('      - "forgeops-v*"', workflow)
        self.assertIn("contents: read", workflow)
        self.assertEqual(1, workflow.count("contents: write"))
        self.assertIn('test "$GITHUB_REF_NAME" = "forgeops-v${version}"', workflow)
        self.assertIn('gh release create "$GITHUB_REF_NAME"', workflow)
        self.assertNotIn("pypi", workflow.lower())

    def test_release_workflow_publishes_only_bounded_assets(self) -> None:
        workflow = (ROOT / ".github/workflows/forgeops-release.yml").read_text()
        self.assertIn("dist/signalforge_forgeops-1.0.0-py3-none-any.whl", workflow)
        self.assertIn("dist/SHA256SUMS.txt", workflow)
        self.assertNotIn("docker", workflow.lower())
        self.assertNotIn("kubectl", workflow.lower())

    def test_release_notes_preserve_authority_boundaries(self) -> None:
        notes = (ROOT / "docs/releases/forgeops-v1.0.0.md").read_text()
        for boundary in ("infer cause", "recommend remediation", "mutate a cluster"):
            self.assertIn(boundary, notes)

    def test_build_ignores_stale_repository_build_content(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            script = ROOT / "scripts" / "build-forgeops-release.py"
            spec = importlib.util.spec_from_file_location("forgeops_release_build", script)
            self.assertIsNotNone(spec)
            self.assertIsNotNone(spec.loader)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            staged = Path(temporary) / "source"
            module.stage_source(ROOT, staged)
            names = {
                path.relative_to(staged).as_posix()
                for path in staged.rglob("*")
                if path.is_file()
            }
            self.assertIn("src/forgeops/cli.py", names)
            self.assertFalse(any(name.startswith("src/foundry_check/") for name in names))
            self.assertFalse(any(name.startswith("build/") for name in names))


if __name__ == "__main__":
    unittest.main()
