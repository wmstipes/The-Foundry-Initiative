from pathlib import Path
import json
import unittest


ROOT = Path(__file__).resolve().parents[1]
CONSOLE = ROOT / "apps" / "forgeops-console"


class ForgeOpsConsoleC2PolicyTests(unittest.TestCase):
    def read(self, relative: str) -> str:
        return (CONSOLE / relative).read_text(encoding="utf-8")

    def test_go_runtime_and_client_go_are_exactly_declared(self) -> None:
        module = self.read("go.mod")
        self.assertIn("go 1.27.0", module)
        self.assertIn("k8s.io/client-go v0.36.4", module)

    def test_browser_dependencies_are_exactly_pinned(self) -> None:
        package = json.loads(self.read("web/package.json"))
        for group in (package["dependencies"], package["devDependencies"]):
            for version in group.values():
                self.assertRegex(version, r"^\d+\.\d+\.\d+$")
                self.assertNotIn("^", version)
                self.assertNotIn("~", version)

    def test_browser_lockfile_is_committed(self) -> None:
        lock = json.loads(self.read("web/package-lock.json"))
        self.assertEqual(lock["lockfileVersion"], 3)
        self.assertEqual(lock["packages"][""]["dependencies"]["react"], "19.3.0")

    def test_configuration_loader_has_no_ambient_fallback(self) -> None:
        loader = self.read("internal/config/loader.go")
        self.assertIn("os.Lstat(path)", loader)
        self.assertNotIn('os.Getenv("KUBECONFIG")', loader)
        self.assertNotIn("ClientConfigLoadingRules", loader)
        self.assertNotIn("InClusterConfig", loader)

    def test_listener_is_restricted_to_literal_loopback(self) -> None:
        server = self.read("internal/server/server.go")
        self.assertIn("ip.IsLoopback()", server)
        self.assertIn("request.Host != a.options.AllowedHost", server)
        self.assertIn('origin.Scheme == "http"', server)

    def test_state_changes_require_an_in_memory_nonce(self) -> None:
        server = self.read("internal/server/server.go")
        browser = self.read("web/src/api.ts")
        self.assertIn("subtle.ConstantTimeCompare", server)
        self.assertIn("X-ForgeOps-Session", server)
        self.assertNotIn("localStorage", browser)
        self.assertNotIn("sessionStorage", browser)

    def test_plugin_registry_is_compiled_and_deny_by_default(self) -> None:
        broker = self.read("internal/broker/broker.go")
        sdk = self.read("web/src/plugin-sdk.tsx")
        self.assertIn("ErrDenied", broker)
        self.assertIn("manifest.Declares(capability)", broker)
        self.assertNotIn("import(", sdk)
        self.assertNotIn("fetch(", sdk)

    def test_cluster_factory_preserves_offline_seam_and_hardens_live_auth(self) -> None:
        factory = self.read("internal/cluster/factory.go")
        self.assertIn("ErrOfflineOnly", factory)
        self.assertNotIn("NewForConfigOrDie", factory)
        self.assertIn("NewNonInteractiveClientConfig", factory)
        self.assertIn("identity.Exec != nil", factory)
        self.assertIn("identity.TokenFile !=", factory)
        self.assertIn("cluster.ProxyURL !=", factory)

    def test_fixture_points_only_to_a_closed_loopback_port(self) -> None:
        fixture = self.read("fixtures/kubeconfig.yaml")
        self.assertIn("server: https://127.0.0.1:65535", fixture)
        self.assertIn("token: synthetic-c2-token-not-a-secret", fixture)

    def test_required_validation_gates_both_console_halves(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "required-validation.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("  console-go:\n", workflow)
        self.assertIn("  console-web:\n", workflow)
        self.assertIn(
            "needs: [python, workbench, console-go, console-web, repository, dependencies]",
            workflow,
        )


if __name__ == "__main__":
    unittest.main()
