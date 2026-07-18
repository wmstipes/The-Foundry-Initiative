from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from foundry_check.cli import main  # noqa: E402


@unittest.skipUnless(shutil.which("git"), "Git is required for repository fixtures")
class CliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.root = Path(self.temporary_directory.name)
        self._create_complete_repository()

    def _create_complete_repository(self) -> None:
        (self.root / "README.md").write_text("# Fixture\n", encoding="utf-8")
        (self.root / ".gitignore").write_text("__pycache__/\n", encoding="utf-8")
        for directory, filename in (("src", "app.py"), ("tests", "test_app.py")):
            path = self.root / directory
            path.mkdir()
            (path / filename).write_text("VALUE = 1\n", encoding="utf-8")
        docs = self.root / "docs"
        docs.mkdir()
        for filename in ("vision.md", "architecture.md", "learning-journal.md"):
            (docs / filename).write_text("# Document\n", encoding="utf-8")
        subprocess.run(
            ["git", "init", "--quiet", str(self.root)],
            check=True, capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(self.root), "add", "."],
            check=True, capture_output=True,
        )

    def test_text_output_and_success_exit_code(self) -> None:
        output = StringIO()
        with redirect_stdout(output):
            exit_code = main([str(self.root)])
        self.assertEqual(0, exit_code)
        self.assertIn("Foundry Check:", output.getvalue())
        self.assertIn("PASS  Required baseline files", output.getvalue())
        self.assertIn("Summary: 5 passed, 0 warning, 0 failed", output.getvalue())

    def test_json_output_has_stable_structure(self) -> None:
        output = StringIO()
        with redirect_stdout(output):
            exit_code = main([str(self.root), "--format", "json"])
        payload = json.loads(output.getvalue())
        self.assertEqual(0, exit_code)
        self.assertEqual("pass", payload["status"])
        self.assertEqual(
            {"passed": 5, "warnings": 0, "failed": 0}, payload["summary"]
        )
        self.assertEqual(5, len(payload["checks"]))

    def test_failed_check_returns_exit_code_one(self) -> None:
        (self.root / "README.md").unlink()
        output = StringIO()
        with redirect_stdout(output):
            exit_code = main([str(self.root)])
        self.assertEqual(1, exit_code)
        self.assertIn("FAIL  Required baseline files", output.getvalue())

    def test_warning_only_returns_exit_code_zero(self) -> None:
        output = StringIO()
        with mock.patch(
            "foundry_check.checks.subprocess.run", side_effect=FileNotFoundError
        ):
            with redirect_stdout(output):
                exit_code = main([str(self.root)])
        self.assertEqual(0, exit_code)
        self.assertIn("WARN  Suspicious tracked secret filenames", output.getvalue())

    def test_invalid_repository_path_returns_exit_code_two(self) -> None:
        missing = self.root / "does-not-exist"
        errors = StringIO()
        with redirect_stderr(errors):
            exit_code = main([str(missing)])
        self.assertEqual(2, exit_code)
        self.assertIn("target path does not exist", errors.getvalue())


if __name__ == "__main__":
    unittest.main()
