from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from foundry_check.checks import (  # noqa: E402
    check_baseline_documentation,
    check_expected_directories,
    check_implementation_and_test_content,
    check_required_baseline_files,
    check_suspicious_tracked_secret_filenames,
    run_checks,
)


class RepositoryFixture:
    def __init__(self, root: Path) -> None:
        self.root = root

    def create_complete(self) -> None:
        (self.root / "README.md").write_text("# Fixture\n", encoding="utf-8")
        (self.root / ".gitignore").write_text("__pycache__/\n", encoding="utf-8")
        (self.root / "src").mkdir()
        (self.root / "src" / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
        (self.root / "tests").mkdir()
        (self.root / "tests" / "test_app.py").write_text(
            "def test_value(): pass\n", encoding="utf-8"
        )
        (self.root / "docs").mkdir()
        for name in ("vision.md", "architecture.md", "learning-journal.md"):
            (self.root / "docs" / name).write_text(f"# {name}\n", encoding="utf-8")

    def initialize_git(self) -> None:
        subprocess.run(
            ["git", "init", "--quiet", str(self.root)],
            check=True, capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(self.root), "add", "."],
            check=True, capture_output=True,
        )


@unittest.skipUnless(shutil.which("git"), "Git is required for repository fixtures")
class CheckTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.root = Path(self.temporary_directory.name)
        self.fixture = RepositoryFixture(self.root)

    def test_fully_passing_repository(self) -> None:
        self.fixture.create_complete()
        self.fixture.initialize_git()
        results = run_checks(self.root)
        self.assertEqual(5, len(results))
        self.assertTrue(all(result.status == "pass" for result in results))

    def test_missing_baseline_files(self) -> None:
        result = check_required_baseline_files(self.root)
        self.assertEqual("fail", result.status)
        self.assertEqual(("README.md", ".gitignore"), result.details)

    def test_missing_expected_directories(self) -> None:
        result = check_expected_directories(self.root)
        self.assertEqual("fail", result.status)
        self.assertEqual(("src", "tests"), result.details)

    def test_gitkeep_only_directories_are_not_substantive(self) -> None:
        for name in ("src", "tests"):
            directory = self.root / name
            directory.mkdir()
            (directory / ".gitkeep").touch()
        result = check_implementation_and_test_content(self.root)
        self.assertEqual("fail", result.status)
        self.assertEqual(("src", "tests"), result.details)

    def test_complete_baseline_documentation(self) -> None:
        docs = self.root / "docs"
        docs.mkdir()
        for name in ("vision.md", "architecture.md", "learning-journal.md"):
            (docs / name).touch()
        result = check_baseline_documentation(self.root)
        self.assertEqual("pass", result.status)

    def test_suspicious_tracked_secret_filename(self) -> None:
        self.fixture.create_complete()
        (self.root / ".env").write_text("not-a-real-secret\n", encoding="utf-8")
        self.fixture.initialize_git()
        result = check_suspicious_tracked_secret_filenames(self.root)
        self.assertEqual("fail", result.status)
        self.assertEqual((".env",), result.details)

    def test_non_git_directory_produces_warning(self) -> None:
        result = check_suspicious_tracked_secret_filenames(self.root)
        self.assertEqual("warning", result.status)
        self.assertIn("not a Git repository", result.message)

    def test_git_unavailable_produces_warning(self) -> None:
        with mock.patch(
            "foundry_check.checks.subprocess.run", side_effect=FileNotFoundError
        ):
            result = check_suspicious_tracked_secret_filenames(self.root)
        self.assertEqual("warning", result.status)
        self.assertIn("unavailable", result.message)


if __name__ == "__main__":
    unittest.main()
