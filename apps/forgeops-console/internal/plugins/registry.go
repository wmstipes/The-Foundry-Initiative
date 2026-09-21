package plugins

import (
	"errors"
	"sort"
)

type Registry struct {
	manifests map[string]Manifest
}

func NewRegistry(manifests ...Manifest) (*Registry, error) {
	registry := &Registry{manifests: make(map[string]Manifest, len(manifests))}
	for _, manifest := range manifests {
		if err := manifest.Validate(); err != nil {
			return nil, err
		}
		if _, exists := registry.manifests[manifest.ID]; exists {
			return nil, errors.New("plugin IDs must be unique")
		}
		registry.manifests[manifest.ID] = cloneManifest(manifest)
	}
	return registry, nil
}

func (r *Registry) Get(id string) (Manifest, bool) {
	manifest, ok := r.manifests[id]
	return cloneManifest(manifest), ok
}

func (r *Registry) Manifests() []Manifest {
	ids := make([]string, 0, len(r.manifests))
	for id := range r.manifests {
		ids = append(ids, id)
	}
	sort.Strings(ids)
	result := make([]Manifest, 0, len(ids))
	for _, id := range ids {
		result = append(result, cloneManifest(r.manifests[id]))
	}
	return result
}

func cloneManifest(manifest Manifest) Manifest {
	manifest.Capabilities = append([]string(nil), manifest.Capabilities...)
	manifest.Contributions = append([]Contribution(nil), manifest.Contributions...)
	return manifest
}
