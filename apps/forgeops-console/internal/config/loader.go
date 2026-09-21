package config

import (
	"errors"
	"fmt"
	"io"
	"os"
	"sort"
	"strings"

	"k8s.io/client-go/tools/clientcmd"
	clientcmdapi "k8s.io/client-go/tools/clientcmd/api"
)

const MaxKubeconfigBytes int64 = 1 << 20

var ErrExplicitKubeconfigRequired = errors.New("an explicit kubeconfig path is required")

type ContextSummary struct {
	Name         string `json:"name"`
	ClusterName  string `json:"clusterName"`
	AuthInfoName string `json:"authInfoName"`
	Namespace    string `json:"namespace"`
}

type Loaded struct {
	Config   *clientcmdapi.Config
	Contexts []ContextSummary
}

// LoadExplicit reads exactly one caller-supplied regular file. It never reads
// KUBECONFIG, a home-directory default, or an in-cluster identity.
func LoadExplicit(path string) (Loaded, error) {
	if strings.TrimSpace(path) == "" {
		return Loaded{}, ErrExplicitKubeconfigRequired
	}

	info, err := os.Lstat(path)
	if err != nil {
		return Loaded{}, fmt.Errorf("inspect explicit kubeconfig: %w", err)
	}
	if info.Mode()&os.ModeSymlink != 0 || !info.Mode().IsRegular() {
		return Loaded{}, errors.New("explicit kubeconfig must be a regular file, not a symlink or special file")
	}
	if info.Size() > MaxKubeconfigBytes {
		return Loaded{}, fmt.Errorf("explicit kubeconfig exceeds %d-byte limit", MaxKubeconfigBytes)
	}

	file, err := os.Open(path)
	if err != nil {
		return Loaded{}, fmt.Errorf("open explicit kubeconfig: %w", err)
	}
	defer file.Close()

	data, err := io.ReadAll(io.LimitReader(file, MaxKubeconfigBytes+1))
	if err != nil {
		return Loaded{}, fmt.Errorf("read explicit kubeconfig: %w", err)
	}
	if int64(len(data)) > MaxKubeconfigBytes {
		return Loaded{}, fmt.Errorf("explicit kubeconfig exceeds %d-byte limit", MaxKubeconfigBytes)
	}

	raw, err := clientcmd.Load(data)
	if err != nil {
		return Loaded{}, fmt.Errorf("parse explicit kubeconfig: %w", err)
	}
	if len(raw.Contexts) == 0 {
		return Loaded{}, errors.New("explicit kubeconfig contains no contexts")
	}

	names := make([]string, 0, len(raw.Contexts))
	for name, context := range raw.Contexts {
		if strings.TrimSpace(name) == "" || context == nil {
			return Loaded{}, errors.New("explicit kubeconfig contains an invalid context")
		}
		names = append(names, name)
	}
	sort.Strings(names)

	contexts := make([]ContextSummary, 0, len(names))
	for _, name := range names {
		context := raw.Contexts[name]
		contexts = append(contexts, ContextSummary{
			Name:         name,
			ClusterName:  context.Cluster,
			AuthInfoName: context.AuthInfo,
			Namespace:    context.Namespace,
		})
	}

	return Loaded{Config: raw, Contexts: contexts}, nil
}
