package plugins

const DiagnosticsPluginID = "forge.diagnostics"

func DiagnosticsManifest() Manifest {
	return Manifest{ID: DiagnosticsPluginID, DisplayName: "Pod diagnostics", Version: "0.1.0", SDKCompatibility: SupportedSDKConstraint,
		Capabilities:  []string{"pods.logs.read", "events.read", "command.preview"},
		Contributions: []Contribution{{ID: "diagnostics.pod", Type: ResourceBrowser, Title: "Bounded Pod diagnostics", Capability: "pods.logs.read"}},
	}
}
