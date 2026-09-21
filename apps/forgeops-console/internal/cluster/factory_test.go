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
