from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch
import urllib.error


spec = importlib.util.spec_from_file_location(
    "publication", Path(__file__).resolve().parents[1] / "scripts/validate-publication.py"
)
publication = importlib.util.module_from_spec(spec)
spec.loader.exec_module(publication)
SHA = "a" * 40


class PublicationGuardTests(unittest.TestCase):
    def setUp(self):
        self.env = {"GITHUB_REPOSITORY": publication.REPOSITORY,
                    "GITHUB_SHA": SHA, "GITHUB_EVENT_NAME": "workflow_dispatch",
                    "GITHUB_REF": "refs/heads/main", "EXPECTED_SOURCE_SHA": SHA}
        self.run = {"id": 42, "head_sha": SHA, "head_branch": "main", "event": "push",
                    "path": ".github/workflows/required-validation.yml",
                    "repository": {"full_name": publication.REPOSITORY},
                    "status": "completed", "conclusion": "success"}
        self.jobs = {"total_count": 1, "jobs": [
            {"name": "Gate 4 required validation", "conclusion": "success"}]}

    def get(self, endpoint):
        return self.jobs if "/jobs?" in endpoint else {"workflow_runs": [self.run]}

    def test_reviewed_main_and_release_tags_are_accepted(self):
        self.assertEqual(publication.validate_context(self.env, SHA), SHA)
        for ref in ["refs/heads/main", "refs/tags/forgeops-v1.0.1",
                    "refs/tags/forge-yaml-workbench-v0.10.1", "refs/tags/v0.7.1"]:
            with self.subTest(ref=ref):
                self.assertEqual(publication.validate_context(
                    self.env | {"GITHUB_EVENT_NAME": "push", "GITHUB_REF": ref}, SHA), SHA)

    def test_wrong_source_ref_repository_and_event_fail_closed(self):
        for change in [{"EXPECTED_SOURCE_SHA": "b" * 40}, {"EXPECTED_SOURCE_SHA": ""},
                       {"GITHUB_REF": "refs/heads/feature"},
                       {"GITHUB_REPOSITORY": "attacker/fork"},
                       {"GITHUB_EVENT_NAME": "pull_request"}, {"GITHUB_SHA": "abc"},
                       {"GITHUB_EVENT_NAME": "push", "GITHUB_REF": "refs/tags/unreviewed"}]:
            with self.subTest(change=change), self.assertRaises(ValueError):
                publication.validate_context(self.env | change, SHA)
        with self.assertRaises(ValueError):
            publication.validate_context(self.env, "b" * 40)

    def test_exact_successful_main_run_and_gate_are_required(self):
        self.assertTrue(publication.validated_main_source(SHA, self.get))
        original = self.run.copy()
        for change in [{"head_sha": "b" * 40}, {"head_branch": "feature"},
                       {"event": "pull_request"}, {"path": "other.yml"},
                       {"repository": {"full_name": "attacker/fork"}},
                       {"status": "in_progress"}, {"conclusion": "failure"}]:
            self.run = original | change
            with self.subTest(change=change):
                self.assertFalse(publication.validated_main_source(SHA, self.get))

    def test_skipped_failed_missing_duplicate_and_truncated_gates_are_rejected(self):
        for jobs in [[], [{"name": "Gate 4 required validation", "conclusion": "skipped"}],
                     [{"name": "Gate 4 required validation", "conclusion": "failure"}],
                     self.jobs["jobs"] * 2]:
            self.jobs = {"total_count": len(jobs), "jobs": jobs}
            self.assertFalse(publication.validated_main_source(SHA, self.get))
        self.jobs = {"total_count": 101, "jobs": []}
        with self.assertRaises(ValueError):
            publication.validated_main_source(SHA, self.get)

    def test_newer_red_run_cannot_use_old_green_evidence(self):
        newer = self.run | {"id": 43, "conclusion": "failure"}
        def get(endpoint):
            return {"workflow_runs": [self.run, newer]}
        self.assertFalse(publication.validated_main_source(SHA, get))

    def test_only_registry_404_allows_a_new_version(self):
        for code in [401, 403, 429, 500]:
            with self.subTest(code=code), patch.object(
                publication.urllib.request, "urlopen",
                side_effect=urllib.error.HTTPError("https://hub.docker.com", code, "error", {}, None)
            ), self.assertRaises(ValueError):
                publication.require_unused_image("wmstipes/signalforge-service-pulse", "0.1.2")
        with patch.object(publication.urllib.request, "urlopen", side_effect=
                          urllib.error.HTTPError("https://hub.docker.com", 404, "missing", {}, None)):
            publication.require_unused_image("wmstipes/signalforge-service-pulse", "0.1.2")
        with patch.object(publication.urllib.request, "urlopen"), self.assertRaises(ValueError):
            publication.require_unused_image("wmstipes/signalforge-service-pulse", "0.1.2")

    def test_unsafe_registry_inputs_do_not_make_network_requests(self):
        with patch.object(publication.urllib.request, "urlopen") as request:
            for image, version in [("other/image", "1.0.0"),
                                   ("wmstipes/image", "1.0.0/../../other"),
                                   ("wmstipes/image", "latest")]:
                with self.assertRaises(ValueError):
                    publication.require_unused_image(image, version)
            request.assert_not_called()

    def test_api_failure_does_not_become_success(self):
        def unavailable(endpoint):
            raise OSError("unavailable")
        with self.assertRaises(OSError):
            publication.validated_main_source(SHA, unavailable)


if __name__ == "__main__":
    unittest.main()
