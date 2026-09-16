from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from forgeops.cli import main  # noqa: E402


class ForgeOpsCliTests(unittest.TestCase):
    def test_context_is_exact_and_checked_before_kubeconfig(self) -> None:
        errors = StringIO()
        with redirect_stderr(errors):
            exit_code = main(["snapshot", "--kubeconfig", "missing", "--context", "wrong"])
        self.assertEqual(2, exit_code)
        self.assertIn("context must exactly match", errors.getvalue())

    def test_missing_kubeconfig_returns_two_without_exposing_path(self) -> None:
        errors = StringIO()
        secret_path = "definitely-missing-sensitive-path"
        with redirect_stderr(errors):
            exit_code = main([
                "snapshot", "--kubeconfig", secret_path,
                "--context", "kubernetes-admin@kubernetes",
            ])
        self.assertEqual(2, exit_code)
        self.assertNotIn(secret_path, errors.getvalue())
        self.assertIn("accessible regular file", errors.getvalue())

    def test_invalid_http_url_stops_before_kubectl_runner(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            kubeconfig = Path(directory) / "config"
            kubeconfig.write_text("fixture", encoding="utf-8")
            errors = StringIO()
            with mock.patch("forgeops.cli.KubectlRunner") as runner:
                with redirect_stderr(errors):
                    exit_code = main([
                        "snapshot", "--kubeconfig", str(kubeconfig),
                        "--context", "kubernetes-admin@kubernetes",
                        "--restaurant-url", "http://user:secret@example.test",
                    ])
            self.assertEqual(2, exit_code)
            runner.assert_not_called()
            self.assertNotIn("secret", errors.getvalue())


if __name__ == "__main__":
    unittest.main()
