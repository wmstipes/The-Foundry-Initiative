package config

import (
	"errors"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

const fixtureKubeconfig = `apiVersion: v1
kind: Config
current-context: ignored-current
clusters:
- name: fixture-cluster
  cluster:
    server: https://127.0.0.1:65535
contexts:
- name: zeta
  context:
    cluster: fixture-cluster
    user: fixture-user
- name: alpha
  context:
    cluster: fixture-cluster
    user: fixture-user
    namespace: forge-test
users:
- name: fixture-user
  user:
    token: fixture-secret-token
`

func writeFixture(t *testing.T, body string) string {
	t.Helper()
	path := filepath.Join(t.TempDir(), "fixture.kubeconfig")
	if err := os.WriteFile(path, []byte(body), 0o600); err != nil {
		t.Fatal(err)
	}
	return path
}

func TestLoadExplicitRequiresPath(t *testing.T) {
	_, err := LoadExplicit("")
	if !errors.Is(err, ErrExplicitKubeconfigRequired) {
		t.Fatalf("expected explicit-path error, got %v", err)
	}
}

func TestLoadExplicitIgnoresAmbientKubeconfigAndSanitizes(t *testing.T) {
	ambient := writeFixture(t, strings.ReplaceAll(fixtureKubeconfig, "alpha", "ambient"))
	t.Setenv("KUBECONFIG", ambient)
	explicit := writeFixture(t, fixtureKubeconfig)

	loaded, err := LoadExplicit(explicit)
	if err != nil {
		t.Fatal(err)
	}
	if len(loaded.Contexts) != 2 || loaded.Contexts[0].Name != "alpha" || loaded.Contexts[1].Name != "zeta" {
		t.Fatalf("contexts were not sanitized and sorted: %#v", loaded.Contexts)
	}
	if loaded.Config.CurrentContext != "ignored-current" {
		t.Fatalf("loader unexpectedly changed current-context: %q", loaded.Config.CurrentContext)
	}
	for _, summary := range loaded.Contexts {
		if strings.Contains(strings.Join([]string{summary.Name, summary.ClusterName, summary.AuthInfoName, summary.Namespace}, " "), "fixture-secret-token") {
			t.Fatal("credential leaked into context summary")
		}
	}
}

func TestLoadExplicitRejectsSymlink(t *testing.T) {
	target := writeFixture(t, fixtureKubeconfig)
	link := filepath.Join(t.TempDir(), "linked.kubeconfig")
	if err := os.Symlink(target, link); err != nil {
		t.Skipf("symlinks unavailable: %v", err)
	}
	if _, err := LoadExplicit(link); err == nil {
		t.Fatal("expected symlink rejection")
	}
}

func TestLoadExplicitRejectsOversizedAndContextlessFiles(t *testing.T) {
	oversized := writeFixture(t, strings.Repeat("x", int(MaxKubeconfigBytes)+1))
	if _, err := LoadExplicit(oversized); err == nil {
		t.Fatal("expected oversized kubeconfig rejection")
	}

	contextless := writeFixture(t, "apiVersion: v1\nkind: Config\n")
	if _, err := LoadExplicit(contextless); err == nil {
		t.Fatal("expected contextless kubeconfig rejection")
	}
}
