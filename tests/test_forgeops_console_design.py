from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARCHITECTURE = ROOT / "docs" / "design" / "forgeops-console-architecture.md"
THREAT_MODEL = ROOT / "docs" / "design" / "forgeops-console-threat-model.md"
PLUGIN_CONTRACT = ROOT / "docs" / "design" / "forgeops-console-plugin-contract.md"
ROADMAP = ROOT / "docs" / "roadmaps" / "forgeops-console-roadmap.md"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class ForgeOpsConsoleDesignTests(unittest.TestCase):
    def test_required_design_documents_exist(self) -> None:
        for path in (ARCHITECTURE, THREAT_MODEL, PLUGIN_CONTRACT, ROADMAP):
            with self.subTest(path=path):
                self.assertTrue(path.is_file())

    def test_architecture_requires_explicit_local_configuration(self) -> None:
        architecture = read_text(ARCHITECTURE)
        self.assertIn("explicit kubeconfig", architecture.lower())
        self.assertIn("binds only to explicit loopback addresses", architecture)
        self.assertIn("must not fall back to `KUBECONFIG`", architecture)
        self.assertIn("must not:\n\n- read, upload, receive, or persist kubeconfig", architecture)

    def test_initial_core_has_no_shell_or_mutation_path(self) -> None:
        architecture = read_text(ARCHITECTURE)
        self.assertIn("does not invoke `kubectl`", architecture)
        self.assertIn("no create, update, patch, apply, delete, scale", architecture)
        self.assertIn("Secrets | Not listed, read, rendered, searched, exported, or requested", architecture)

    def test_plugin_contract_is_strict_and_brokered(self) -> None:
        contract = read_text(PLUGIN_CONTRACT)
        self.assertIn("apiVersion: console.forgeops.io/v1alpha1", contract)
        self.assertIn("unknown fields fail validation", contract)
        self.assertIn("the core must support it", contract)
        self.assertIn("cannot declare arbitrary Kubernetes resources", contract)

    def test_dynamic_and_third_party_plugins_are_deferred(self) -> None:
        architecture = read_text(ARCHITECTURE)
        contract = read_text(PLUGIN_CONTRACT)
        self.assertIn("prohibit runtime downloads", architecture)
        self.assertIn("third-party plugins", contract)
        self.assertIn("deferred", contract.lower())

    def test_threat_model_covers_primary_authority_failures(self) -> None:
        threat_model = read_text(THREAT_MODEL)
        for heading in (
            "Credential disclosure",
            "Wrong-cluster or wrong-namespace action",
            "Excessive Kubernetes authority",
            "Malicious or compromised plugin",
            "Browser attacks and loopback abuse",
            "Evidence overclaim or cross-contract confusion",
        ):
            with self.subTest(heading=heading):
                self.assertIn(f"### {heading}", threat_model)

    def test_roadmap_preserves_existing_numbered_work(self) -> None:
        roadmap = read_text(ROADMAP)
        self.assertIn("do not renumber the\npublished ForgeOps Milestones 066-088", roadmap)
        for work_package in range(1, 8):
            self.assertIn(f"### C{work_package} —", roadmap)

    def test_forgeops_v1_remains_independent_and_immutable(self) -> None:
        architecture = read_text(ARCHITECTURE)
        roadmap = read_text(ROADMAP)
        self.assertIn("ForgeOps v1.0.0 and its\npublic artifacts remain unchanged", architecture)
        self.assertIn("ForgeOps v1.0.0 remains immutable and independently usable", roadmap)


if __name__ == "__main__":
    unittest.main()
