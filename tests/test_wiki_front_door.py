from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "scripts" / "validate-wiki-front-door.py"
SPEC = importlib.util.spec_from_file_location("validate_wiki_front_door", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
validator = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = validator
SPEC.loader.exec_module(validator)


class WikiFrontDoorTests(unittest.TestCase):
    def test_repository_front_door_passes(self) -> None:
        result = validator.validate_front_door(REPO_ROOT)
        self.assertEqual((), result.errors)

    def test_approved_trigger_matrix(self) -> None:
        cases = (
            ("documentation push", "push", "refs/heads/main", ("README.md",), False),
            (
                "Wiki source push",
                "push",
                "refs/heads/main",
                ("docs/wiki/Home.md",),
                False,
            ),
            (
                "Restaurant source push",
                "push",
                "refs/heads/main",
                ("apps/restaurant-api/main.py",),
                True,
            ),
            ("version tag", "push", "refs/tags/v0.8.0", (), True),
            ("manual dispatch", "workflow_dispatch", "", (), True),
        )
        for name, event, ref, changed_paths, expected in cases:
            with self.subTest(name=name):
                self.assertEqual(
                    expected,
                    validator.restaurant_workflow_should_run(
                        event=event, ref=ref, changed_paths=changed_paths
                    ),
                )

    def test_missing_source_notice_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self._copy_minimal_repository(Path(temporary))
            home = root / "docs" / "wiki" / "Home.md"
            home.write_text(
                home.read_text(encoding="utf-8").replace(validator.SOURCE_NOTICE, ""),
                encoding="utf-8",
            )
            result = validator.validate_front_door(root)
            self.assertTrue(
                any("authoritative-source notice" in error for error in result.errors)
            )

    def test_missing_repository_target_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self._copy_minimal_repository(Path(temporary))
            home = root / "docs" / "wiki" / "Home.md"
            home.write_text(
                home.read_text(encoding="utf-8").replace(
                    "/blob/main/README.md", "/blob/main/DOES-NOT-EXIST.md"
                ),
                encoding="utf-8",
            )
            result = validator.validate_front_door(root)
            self.assertTrue(any("does not exist" in error for error in result.errors))

    def test_heading_level_skip_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self._copy_minimal_repository(Path(temporary))
            home = root / "docs" / "wiki" / "Home.md"
            home.write_text(
                home.read_text(encoding="utf-8").replace(
                    "## Choose your path", "### Choose your path"
                ),
                encoding="utf-8",
            )
            result = validator.validate_front_door(root)
            self.assertTrue(any("heading level skips" in error for error in result.errors))

    def test_volatile_operational_content_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self._copy_minimal_repository(Path(temporary))
            home = root / "docs" / "wiki" / "Home.md"
            home.write_text(
                home.read_text(encoding="utf-8")
                + "\nThe live release is `0.10.0` at 192.168.1.10.\n",
                encoding="utf-8",
            )
            result = validator.validate_front_door(root)
            self.assertTrue(any("release version" in error for error in result.errors))
            self.assertTrue(any("private IPv4 address" in error for error in result.errors))

    def test_wiki_copy_must_match_source(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            wiki = Path(temporary)
            for name in validator.EXPECTED_WIKI_FILES:
                source = REPO_ROOT / "docs" / "wiki" / name
                (wiki / name).write_bytes(source.read_bytes())
            self.assertTrue(validator.compare_wiki_copy(REPO_ROOT, wiki).ok)
            (wiki / "Home.md").write_text("changed\n", encoding="utf-8")
            result = validator.compare_wiki_copy(REPO_ROOT, wiki)
            self.assertIn(
                "Wiki checkout differs from repository source: Home.md", result.errors
            )

    def _copy_minimal_repository(self, root: Path) -> Path:
        for relative in (
            "README.md",
            "ROADMAP.md",
            "docs/project-status.md",
            "docs/architecture.md",
            "docs/vision.md",
            ".github/workflows/restaurant-api-docker.yml",
        ):
            source = REPO_ROOT / relative
            destination = root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(source.read_bytes())
        for directory in ("docs/runbooks", "docs/milestones", "docs/wiki"):
            (root / directory).mkdir(parents=True, exist_ok=True)
        for name in validator.EXPECTED_WIKI_FILES:
            source = REPO_ROOT / "docs" / "wiki" / name
            (root / "docs" / "wiki" / name).write_bytes(source.read_bytes())
        return root


if __name__ == "__main__":
    unittest.main()
