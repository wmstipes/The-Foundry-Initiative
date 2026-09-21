package plugins

import "testing"

func TestExampleManifestIsValid(t *testing.T) {
	if err := ExampleManifest().Validate(); err != nil {
		t.Fatalf("example manifest is invalid: %v", err)
	}
}

func TestManifestRejectsUnsafeDeclarations(t *testing.T) {
	tests := []struct {
		name   string
		mutate func(*Manifest)
	}{
		{"invalid ID", func(m *Manifest) { m.ID = "UPPER" }},
		{"invalid version", func(m *Manifest) { m.Version = "latest" }},
		{"incompatible SDK", func(m *Manifest) { m.SDKCompatibility = ">=1.0.0" }},
		{"duplicate capability", func(m *Manifest) { m.Capabilities = append(m.Capabilities, m.Capabilities[0]) }},
		{"dynamic contribution", func(m *Manifest) { m.Contributions[0].Type = "remoteModule" }},
		{"undeclared capability", func(m *Manifest) { m.Contributions[0].Capability = "cluster.read" }},
	}
	for _, test := range tests {
		t.Run(test.name, func(t *testing.T) {
			manifest := ExampleManifest()
			test.mutate(&manifest)
			if err := manifest.Validate(); err == nil {
				t.Fatal("expected validation error")
			}
		})
	}
}

func TestRegistryRejectsDuplicatePlugin(t *testing.T) {
	manifest := ExampleManifest()
	if _, err := NewRegistry(manifest, manifest); err == nil {
		t.Fatal("expected duplicate plugin error")
	}
}

func TestRegistryDefensivelyCopiesManifests(t *testing.T) {
	manifest := ExampleManifest()
	registry, err := NewRegistry(manifest)
	if err != nil {
		t.Fatal(err)
	}
	manifest.Capabilities[0] = "cluster.read"
	retrieved, ok := registry.Get(ExamplePluginID)
	if !ok {
		t.Fatal("example plugin missing")
	}
	retrieved.Capabilities[0] = "cluster.write"
	again, _ := registry.Get(ExamplePluginID)
	if again.Capabilities[0] != ExampleStatusCapability {
		t.Fatalf("registry manifest was mutated: %#v", again)
	}
}
