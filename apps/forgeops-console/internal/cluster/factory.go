package cluster

import (
	"context"
	"errors"
	"strings"

	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/rest"
	"k8s.io/client-go/tools/clientcmd"
	clientcmdapi "k8s.io/client-go/tools/clientcmd/api"
)

var (
	ErrOfflineOnly       = errors.New("offline mode does not construct live Kubernetes clients")
	ErrUnsupportedAuth   = errors.New("kubeconfig uses an unsupported external authentication mechanism")
	ErrUnsupportedConfig = errors.New("kubeconfig uses an unsupported transport mechanism")
)

type ClientFactory interface {
	ClientFor(context.Context, *clientcmdapi.Config, string) (kubernetes.Interface, error)
}

type ClientFactoryFunc func(context.Context, *clientcmdapi.Config, string) (kubernetes.Interface, error)

func (function ClientFactoryFunc) ClientFor(ctx context.Context, config *clientcmdapi.Config, contextName string) (kubernetes.Interface, error) {
	return function(ctx, config, contextName)
}

type OfflineFactory struct{}

func (OfflineFactory) ClientFor(context.Context, *clientcmdapi.Config, string) (kubernetes.Interface, error) {
	return nil, ErrOfflineOnly
}

// LiveFactory creates a typed client from one already-loaded explicit
// kubeconfig. It deliberately rejects all secondary files, exec plugins,
// auth-provider plugins, proxies, and insecure TLS.
type LiveFactory struct{}

func (LiveFactory) ClientFor(ctx context.Context, raw *clientcmdapi.Config, contextName string) (kubernetes.Interface, error) {
	if err := ctx.Err(); err != nil {
		return nil, err
	}
	if err := validate(raw, contextName); err != nil {
		return nil, err
	}
	overrides := &clientcmd.ConfigOverrides{CurrentContext: contextName}
	clientConfig := clientcmd.NewNonInteractiveClientConfig(*raw.DeepCopy(), contextName, overrides, nil)
	restConfig, err := clientConfig.ClientConfig()
	if err != nil {
		return nil, ErrUnsupportedConfig
	}
	restConfig.Timeout = 5 * 1e9
	httpClient, err := rest.HTTPClientFor(restConfig)
	if err != nil {
		return nil, ErrUnsupportedConfig
	}
	return kubernetes.NewForConfigAndClient(restConfig, httpClient)
}

func validate(raw *clientcmdapi.Config, contextName string) error {
	if raw == nil || strings.TrimSpace(contextName) == "" {
		return ErrUnsupportedConfig
	}
	selected := raw.Contexts[contextName]
	if selected == nil {
		return ErrUnsupportedConfig
	}
	cluster := raw.Clusters[selected.Cluster]
	identity := raw.AuthInfos[selected.AuthInfo]
	if cluster == nil || identity == nil || strings.TrimSpace(cluster.Server) == "" {
		return ErrUnsupportedConfig
	}
	if cluster.InsecureSkipTLSVerify || cluster.ProxyURL != "" || cluster.CertificateAuthority != "" {
		return ErrUnsupportedConfig
	}
	if identity.Exec != nil || identity.AuthProvider != nil || identity.TokenFile != "" || identity.ClientCertificate != "" || identity.ClientKey != "" {
		return ErrUnsupportedAuth
	}
	if len(cluster.CertificateAuthorityData) == 0 {
		return ErrUnsupportedConfig
	}
	if identity.Impersonate != "" || len(identity.ImpersonateGroups) != 0 || len(identity.ImpersonateUserExtra) != 0 {
		return ErrUnsupportedAuth
	}
	return nil
}
