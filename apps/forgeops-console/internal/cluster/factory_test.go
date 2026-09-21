package cluster

import (
	"context"
	"errors"
	"testing"

	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/kubernetes/fake"
	clientcmdapi "k8s.io/client-go/tools/clientcmd/api"
)

func TestOfflineFactoryCannotConstructClient(t *testing.T) {
	client, err := (OfflineFactory{}).ClientFor(context.Background(), &clientcmdapi.Config{}, "fixture")
	if client != nil || !errors.Is(err, ErrOfflineOnly) {
		t.Fatalf("expected offline-only rejection, client=%v err=%v", client, err)
	}
}

func TestFactorySeamAcceptsOnlyAnInjectedFakeInC2Tests(t *testing.T) {
	factory := ClientFactoryFunc(func(context.Context, *clientcmdapi.Config, string) (kubernetes.Interface, error) {
		return fake.NewSimpleClientset(), nil
	})
	client, err := factory.ClientFor(context.Background(), &clientcmdapi.Config{}, "fixture")
	if err != nil {
		t.Fatal(err)
	}
	list, err := client.CoreV1().Namespaces().List(context.Background(), metav1.ListOptions{})
	if err != nil || len(list.Items) != 0 {
		t.Fatalf("unexpected fake-client result: %#v, %v", list, err)
	}
}

func TestLiveFactoryRejectsExternalAndActiveCredentialMechanisms(t *testing.T) {
	base := func() *clientcmdapi.Config {
		return &clientcmdapi.Config{
			Contexts:  map[string]*clientcmdapi.Context{"dev": {Cluster: "cluster", AuthInfo: "user"}},
			Clusters:  map[string]*clientcmdapi.Cluster{"cluster": {Server: "https://127.0.0.1:65535", CertificateAuthorityData: []byte("ca")}},
			AuthInfos: map[string]*clientcmdapi.AuthInfo{"user": {Token: "embedded"}},
		}
	}
	config := base()
	config.AuthInfos["user"].TokenFile = "/tmp/token"
	if _, err := (LiveFactory{}).ClientFor(context.Background(), config, "dev"); !errors.Is(err, ErrUnsupportedAuth) {
		t.Fatalf("expected token-file rejection, got %v", err)
	}
	config = base()
	config.Clusters["cluster"].ProxyURL = "http://127.0.0.1:8888"
	if _, err := (LiveFactory{}).ClientFor(context.Background(), config, "dev"); !errors.Is(err, ErrUnsupportedConfig) {
		t.Fatalf("expected proxy rejection, got %v", err)
	}
	config = base()
	config.Clusters["cluster"].InsecureSkipTLSVerify = true
	if _, err := (LiveFactory{}).ClientFor(context.Background(), config, "dev"); !errors.Is(err, ErrUnsupportedConfig) {
		t.Fatalf("expected insecure TLS rejection, got %v", err)
	}
}
