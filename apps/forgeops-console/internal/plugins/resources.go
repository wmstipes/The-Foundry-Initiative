package plugins

const (
	ResourcesPluginID       = "forge.resources"
	ResourcesReadCapability = "resources.read"
	ResourcesContributionID = "resources.browser"
)

func ResourcesManifest() Manifest {
	return Manifest{
		ID:               ResourcesPluginID,
		DisplayName:      "Kubernetes resources",
		Version:          "0.1.0",
		SDKCompatibility: SupportedSDKConstraint,
		Capabilities:     []string{ResourcesReadCapability},
		Contributions: []Contribution{{
			ID:         ResourcesContributionID,
			Type:       ResourceBrowser,
			Title:      "Read-only resources",
			Capability: ResourcesReadCapability,
		}},
	}
}
