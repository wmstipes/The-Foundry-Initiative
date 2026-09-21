from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CONSOLE = ROOT / "apps" / "forgeops-console"


class ForgeOpsConsoleC3PolicyTests(unittest.TestCase):
    def read(self, relative: str) -> str:
        return (CONSOLE / relative).read_text(encoding="utf-8")

    def test_resource_allowlist_and_limits_are_fixed(self) -> None:
        service = self.read("internal/resources/service.go")
        for resource in ("namespaces", "nodes", "deployments", "replicasets", "pods", "services", "endpointslices"):
            self.assertIn(f'"{resource}": true', service)
        self.assertIn("RequestTimeout   = 5 * time.Second", service)
        self.assertIn("MaxConcurrent    = 4", service)
        self.assertIn("MaxObjects       = 200", service)
        self.assertIn("MaxResponseBytes = 1 << 20", service)
        self.assertNotIn("DynamicClient", service)

    def test_projection_excludes_sensitive_resource_families(self) -> None:
        service = self.read("internal/resources/service.go")
        for forbidden in ("Secrets(", "ConfigMaps(", "Events(", "Logs(", "Exec("):
            self.assertNotIn(forbidden, service)
        self.assertNotIn("Annotations", service)

    def test_scope_generation_and_stale_cancellation_are_explicit(self) -> None:
        state = self.read("internal/session/state.go")
        service = self.read("internal/resources/service.go")
        self.assertIn("scope.Generation++", state)
        self.assertIn("s.cancelScope()", state)
        self.assertIn("ErrStaleScope", state)
        self.assertIn("current.Generation != scope.Generation", service)

    def test_demo_is_synthetic_and_separate_from_production_entrypoint(self) -> None:
        production = self.read("cmd/forgeops-console/main.go")
        demo = self.read("cmd/forgeops-console-demo/main.go")
        self.assertIn("cluster.LiveFactory{}", production)
        self.assertNotIn("fake.NewSimpleClientset", production)
        self.assertIn("fake.NewSimpleClientset", demo)
        self.assertIn('Mode: "synthetic-demo"', demo)
        self.assertNotIn("LoadExplicit", demo)

    def test_browser_has_no_arbitrary_kubernetes_request_surface(self) -> None:
        api = self.read("web/src/api.ts")
        self.assertIn('"/api/v1/plugins/forge.resources/query"', api)
        self.assertNotIn("kubectl", api)
        self.assertNotIn("localStorage", api)
        self.assertNotIn("sessionStorage", api)


if __name__ == "__main__":
    unittest.main()
