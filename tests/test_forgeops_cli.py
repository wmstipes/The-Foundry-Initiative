from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from forgeops.cli import build_parser, main  # noqa: E402
from forgeops.constants import EXPECTED_CONTEXT, SCHEMA_VERSION  # noqa: E402
from forgeops.models import CheckResult, Evidence, EvaluatedSnapshot, RawSnapshot, Status  # noqa: E402


class ForgeOpsCliTests(unittest.TestCase):
    def test_evidence_validation_command_is_explicitly_supported(self) -> None:
        args = build_parser().parse_args([
            "evidence", "validate", "--input", "snapshot.json",
        ])
        self.assertEqual("evidence", args.command)
        self.assertEqual("validate", args.evidence_command)
        self.assertEqual("snapshot.json", args.input)

    def test_json_output_format_is_explicitly_supported(self) -> None:
        args = build_parser().parse_args([
            "snapshot", "--kubeconfig", "fixture",
            "--context", "kubernetes-admin@kubernetes", "--format", "json",
        ])
        self.assertEqual("json", args.output_format)

    def test_json_format_renders_evaluated_snapshot_without_live_collection(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            kubeconfig = Path(directory) / "config"
            kubeconfig.write_text("fixture", encoding="utf-8")
            raw = RawSnapshot(
                SCHEMA_VERSION,
                "2026-09-16T18:00:00Z",
                EXPECTED_CONTEXT,
                (Evidence("context", "kubectl config current-context", EXPECTED_CONTEXT),),
            )
            evaluated = EvaluatedSnapshot(
                SCHEMA_VERSION,
                "2026-09-16T18:00:00Z",
                EXPECTED_CONTEXT,
                (
                    CheckResult(
                        "context", Status.PASS, "Exact Kubernetes context matched",
                        "kubectl config current-context", "2026-09-16T18:00:00Z",
                        EXPECTED_CONTEXT, EXPECTED_CONTEXT,
                    ),
                ),
            )
            output = StringIO()
            with mock.patch("forgeops.cli.KubectlRunner"), \
                    mock.patch("forgeops.cli.Collector") as collector, \
                    mock.patch("forgeops.cli.evaluate", return_value=evaluated):
                collector.return_value.collect.return_value = raw
                with redirect_stdout(output):
                    exit_code = main([
                        "snapshot", "--kubeconfig", str(kubeconfig),
                        "--context", EXPECTED_CONTEXT, "--format", "json",
                    ])
            payload = json.loads(output.getvalue())
            self.assertEqual(0, exit_code)
            self.assertEqual(SCHEMA_VERSION, payload["schema"])
            self.assertEqual(["context"], [check["id"] for check in payload["checks"]])
            self.assertEqual("PASS", payload["summary"]["overallStatus"])

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
