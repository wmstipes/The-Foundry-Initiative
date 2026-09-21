package cluster

import (
	"context"
	"errors"

	"k8s.io/client-go/kubernetes"
	clientcmdapi "k8s.io/client-go/tools/clientcmd/api"
)

var ErrOfflineOnly = errors.New("C2 does not construct live Kubernetes clients")

type ClientFactory interface {
	ClientFor(context.Context, *clientcmdapi.Config, string) (kubernetes.Interface, error)
}

type ClientFactoryFunc func(context.Context, *clientcmdapi.Config, string) (kubernetes.Interface, error)

func (function ClientFactoryFunc) ClientFor(ctx context.Context, config *clientcmdapi.Config, contextName string) (kubernetes.Interface, error) {
	return function(ctx, config, contextName)
}

// OfflineFactory makes the C2 boundary explicit. C3 must separately replace
// it with a reviewed client-go factory before any live connection is possible.
type OfflineFactory struct{}

func (OfflineFactory) ClientFor(context.Context, *clientcmdapi.Config, string) (kubernetes.Interface, error) {
	return nil, ErrOfflineOnly
}
