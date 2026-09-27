package cluster

import (
	"context"
	"errors"
	"time"

	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/rest"
	clientcmdapi "k8s.io/client-go/tools/clientcmd/api"
)

// InClusterFactory uses only the Pod's projected ServiceAccount token and
// Kubernetes CA. It accepts the single synthetic "forge" context; no browser
// supplied context can select another cluster or identity.
type InClusterFactory struct{}

func (InClusterFactory) ClientFor(ctx context.Context, _ *clientcmdapi.Config, contextName string) (kubernetes.Interface, error) {
	if err := ctx.Err(); err != nil {
		return nil, err
	}
	if contextName != "forge" {
		return nil, errors.New("unknown in-cluster context")
	}
	cfg, err := rest.InClusterConfig()
	if err != nil {
		return nil, err
	}
	cfg.Timeout = 5 * time.Second
	httpClient, err := rest.HTTPClientFor(cfg)
	if err != nil {
		return nil, err
	}
	return kubernetes.NewForConfigAndClient(cfg, httpClient)
}
