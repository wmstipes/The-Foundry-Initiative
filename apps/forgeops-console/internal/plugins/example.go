package plugins

const (
	ExamplePluginID         = "forge.example"
	ExampleStatusCapability = "example.status"
)

func ExampleManifest() Manifest {
	return Manifest{
		ID:               ExamplePluginID,
		DisplayName:      "Example Status",
		Version:          "0.1.0",
		SDKCompatibility: SupportedSDKConstraint,
		Capabilities:     []string{ExampleStatusCapability},
		Contributions: []Contribution{{
			ID:         "example.card",
			Type:       DashboardCard,
			Title:      "Offline plugin status",
			Capability: ExampleStatusCapability,
		}},
	}
}
