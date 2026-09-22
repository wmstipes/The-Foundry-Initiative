// Package console identifies a matched first-party source bundle.
// The digest detects mixed builds; it is not publisher authentication.
package console

import (
	"crypto/sha256"
	"embed"
	"encoding/hex"
	"io"
	"io/fs"
	"sort"
	"sync"
)

// Keep these inputs aligned with web/vite.config.ts. Generated output is excluded.
//
//go:embed bundle.go go.mod go.sum internal/*/*.go cmd/*/*.go web/src/*.ts web/src/*.tsx web/src/*.css web/src/plugins/*.tsx web/index.html web/package.json web/package-lock.json web/tsconfig.json web/tsconfig.app.json web/tsconfig.node.json web/vite.config.ts
var source embed.FS

type BundleIdentity struct {
	Protocol     string `json:"protocol"`
	SourceDigest string `json:"sourceDigest"`
}

var identity BundleIdentity
var once sync.Once

func Bundle() BundleIdentity {
	once.Do(func() {
		var paths []string
		if err := fs.WalkDir(source, ".", func(path string, entry fs.DirEntry, err error) error {
			if err != nil {
				return err
			}
			if !entry.IsDir() {
				paths = append(paths, path)
			}
			return nil
		}); err != nil {
			panic("embedded bundle unavailable")
		}
		sort.Strings(paths)
		digest := sha256.New()
		for _, path := range paths {
			data, err := source.ReadFile(path)
			if err != nil {
				panic("embedded bundle unavailable")
			}
			io.WriteString(digest, path)
			digest.Write([]byte{0})
			digest.Write(data)
			digest.Write([]byte{0})
		}
		identity = BundleIdentity{Protocol: "forgeops.console/v1alpha1", SourceDigest: hex.EncodeToString(digest.Sum(nil))}
	})
	return identity
}
