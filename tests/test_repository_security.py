from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_DIR = ROOT / ".github" / "workflows"
WORKFLOW_FILES = tuple(sorted(WORKFLOW_DIR.glob("*.y*ml")))
TRUSTED_ACTION_OWNERS = {"actions", "docker"}


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


class RepositorySecurityPolicyTests(unittest.TestCase):
    def test_every_workflow_declares_read_only_contents_by_default(self) -> None:
        self.assertTrue(WORKFLOW_FILES)
        for path in WORKFLOW_FILES:
            with self.subTest(workflow=path.name):
                text = read_text(path)
                match = re.search(
                    r"(?m)^permissions:\s*$\n(?P<body>(?:^[ \t]+[^\n]*\n?)*)",
                    text,
                )
                self.assertIsNotNone(match, "missing top-level permissions block")
                self.assertIn(
                    "contents: read",
                    match.group("body"),
                    "top-level permissions must default contents to read",
                )

    def test_reusable_actions_are_trusted_and_pinned_to_full_commit_shas(self) -> None:
        uses_pattern = re.compile(
            r"(?m)^\s*(?:-\s+)?uses:\s+(?P<action>[^@\s]+)@(?P<ref>[^\s#]+)"
        )
        for path in WORKFLOW_FILES:
            for match in uses_pattern.finditer(read_text(path)):
                action = match.group("action")
                if action.startswith("./"):
                    continue
                with self.subTest(workflow=path.name, action=action):
                    self.assertIn(action.split("/", 1)[0], TRUSTED_ACTION_OWNERS)
                    self.assertRegex(match.group("ref"), r"^[0-9a-f]{40}$")

    def test_workflows_do_not_use_privileged_pull_request_target(self) -> None:
        for path in WORKFLOW_FILES:
            with self.subTest(workflow=path.name):
                self.assertNotRegex(read_text(path), r"(?m)^\s*pull_request_target:")

    def test_only_release_publish_job_has_write_permission(self) -> None:
        write_permissions: list[tuple[str, str]] = []
        for path in WORKFLOW_FILES:
            for match in re.finditer(
                r"(?m)^\s+(?P<scope>[a-z-]+):\s+write\s*$", read_text(path)
            ):
                write_permissions.append((path.name, match.group("scope")))
        self.assertEqual(write_permissions, [("forgeops-release.yml", "contents")])

    def test_dependabot_covers_every_managed_dependency_ecosystem(self) -> None:
        config = read_text(ROOT / ".github" / "dependabot.yml")
        configured = set(
            re.findall(
                r'- package-ecosystem: "([^"]+)"\n\s+directory: "([^"]+)"',
                config,
            )
        )
        self.assertEqual(
            configured,
            {
                ("github-actions", "/"),
                ("pip", "/"),
                ("pip", "/apps/restaurant-api"),
                ("npm", "/apps/forge-yaml-workbench"),
                ("docker", "/apps/restaurant-api"),
                ("docker", "/apps/forge-yaml-workbench"),
            },
        )

    def test_security_policy_uses_private_reporting(self) -> None:
        policy = read_text(ROOT / "SECURITY.md")
        self.assertIn("/security/advisories/new", policy)
        self.assertIn("do not open a public issue", policy.lower())


if __name__ == "__main__":
    unittest.main()
