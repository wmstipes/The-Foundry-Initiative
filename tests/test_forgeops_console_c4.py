from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
CONSOLE = ROOT / "apps" / "forgeops-console"


class ForgeOpsConsoleC4PolicyTests(unittest.TestCase):
    def read(self, relative: str) -> str:
        return (CONSOLE / relative).read_text(encoding="utf-8")

    def test_diagnostics_are_brokered_with_fixed_capabilities(self):
        manifest = self.read("internal/plugins/diagnostics.go")
        for capability in ("pods.logs.read", "events.read", "command.preview"):
            self.assertIn(capability, manifest)
        server = self.read("internal/server/server.go")
        self.assertIn("plugins.DiagnosticsPluginID, capability", server)
        self.assertIn('POST /api/v1/plugins/forge.diagnostics/query', server)

    def test_diagnostics_have_no_execution_or_export_path(self):
        service = self.read("internal/diagnostics/service.go")
        for forbidden in ('"os/exec"', "Secrets(", "ConfigMaps(", "Watch(", "Follow: true"):
            self.assertNotIn(forbidden, service)
        self.assertIn("io.LimitReader", service)
        self.assertIn("context.AfterFunc", service)
        self.assertIn("involvedObject.uid", service)

    def test_browser_diagnostics_are_inert_and_cancellable(self):
        panel = self.read("web/src/plugins/diagnostics.tsx")
        for forbidden in ("dangerouslySetInnerHTML", "localStorage", "sessionStorage", "eval("):
            self.assertNotIn(forbidden, panel)
        self.assertIn("AbortController", panel)
        self.assertIn("serial.current", panel)
        self.assertIn("not guaranteed redacted", panel)

    def test_c4_milestone_preserves_separate_live_authority(self):
        milestone = (ROOT / "docs/milestones/forgeops-console-c4-pod-diagnostics.md").read_text(encoding="utf-8")
        self.assertIn("separate authorization", milestone)
        self.assertIn("not executed", milestone)


if __name__ == "__main__":
    unittest.main()
