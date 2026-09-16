from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from forgeops.collect import validate_kubeconfig  # noqa: E402
from forgeops.runners import HttpRunner, KubectlRunner, Operation, RunnerFailure  # noqa: E402


class ForgeOpsRunnerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.runner = KubectlRunner(Path("/explicit/config"), "kubernetes-admin@kubernetes")

    def test_command_vectors_are_fixed_and_use_explicit_target(self) -> None:
        command = self.runner._command(Operation.PODS, ("forge-restaurant", "restaurant-api"))
        self.assertEqual("kubectl", command[0])
        self.assertIn("/explicit/config", command)
        self.assertIn("kubernetes-admin@kubernetes", command)
        self.assertEqual(["get", "pods", "-n", "forge-restaurant", "-l", "app=restaurant-api", "-o", "json"], command[-8:])

    def test_non_allowlisted_target_is_rejected_before_subprocess(self) -> None:
        with mock.patch("forgeops.runners.subprocess.run") as run:
            with self.assertRaises(RunnerFailure) as caught:
                self.runner.run_json(Operation.DEPLOYMENT, ("default", "anything"))
        self.assertEqual("unsafe-operation", caught.exception.detail.category)
        run.assert_not_called()

    def test_subprocess_never_uses_shell(self) -> None:
        completed = subprocess.CompletedProcess([], 0, b"{}", b"")
        with mock.patch("forgeops.runners.subprocess.run", return_value=completed) as run:
            self.runner.run_json(Operation.VERSION)
        self.assertIs(False, run.call_args.kwargs["shell"])

    def test_malformed_and_oversized_output_fail_closed(self) -> None:
        malformed = subprocess.CompletedProcess([], 0, b"not-json", b"")
        with mock.patch("forgeops.runners.subprocess.run", return_value=malformed):
            with self.assertRaises(RunnerFailure) as caught:
                self.runner.run_json(Operation.VERSION)
        self.assertEqual("malformed-json", caught.exception.detail.category)
        oversized = subprocess.CompletedProcess([], 0, b"x" * (2 * 1024 * 1024 + 1), b"")
        with mock.patch("forgeops.runners.subprocess.run", return_value=oversized):
            with self.assertRaises(RunnerFailure) as caught:
                self.runner.run_json(Operation.VERSION)
        self.assertEqual("oversized-output", caught.exception.detail.category)

    def test_error_text_is_bounded_and_redacted(self) -> None:
        completed = subprocess.CompletedProcess([], 1, b"", b"token=secret " + b"x" * 5000)
        with mock.patch("forgeops.runners.subprocess.run", return_value=completed):
            with self.assertRaises(RunnerFailure) as caught:
                self.runner.run_json(Operation.VERSION)
        self.assertNotIn("secret", caught.exception.detail.summary)
        self.assertLessEqual(len(caught.exception.detail.summary.encode()), 2048)

    def test_explicit_kubeconfig_must_be_regular_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(RunnerFailure):
                validate_kubeconfig(directory)
            file_path = Path(directory) / "config"
            file_path.write_text("fixture", encoding="utf-8")
            self.assertEqual(file_path.resolve(), validate_kubeconfig(str(file_path)))

    def test_http_url_validation_rejects_credentials_and_non_http(self) -> None:
        for url in (
            "file:///tmp/data",
            "http://user:pass@example.test",
            "http://example.test/unexpected",
            "example.test",
        ):
            with self.subTest(url=url), self.assertRaises(RunnerFailure):
                HttpRunner.validate_base_url(url)
        self.assertEqual("https://example.test:30080", HttpRunner.validate_base_url("https://example.test:30080/"))


if __name__ == "__main__":
    unittest.main()
