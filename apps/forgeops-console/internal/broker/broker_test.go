package broker

import (
	"context"
	"errors"
	"testing"

	"github.com/wmstipes/The-Foundry-Initiative/apps/forgeops-console/internal/plugins"
)

func newBroker(t *testing.T) *Broker {
	t.Helper()
	registry, err := plugins.NewRegistry(plugins.ExampleManifest())
	if err != nil {
		t.Fatal(err)
	}
	result, err := New(registry)
	if err != nil {
		t.Fatal(err)
	}
	return result
}

func TestBrokerDeniesUnknownAndUnregisteredCapabilities(t *testing.T) {
	b := newBroker(t)
	for _, pluginID := range []string{"missing", plugins.ExamplePluginID} {
		if _, err := b.Invoke(context.Background(), pluginID, plugins.ExampleStatusCapability, Request{}); !errors.Is(err, ErrDenied) {
			t.Fatalf("expected denial for %q, got %v", pluginID, err)
		}
	}
	if err := b.Register(plugins.ExamplePluginID, "cluster.read", func(context.Context, Request) (Response, error) { return Response{}, nil }); !errors.Is(err, ErrDenied) {
		t.Fatalf("expected undeclared capability denial, got %v", err)
	}
}

func TestBrokerInvokesDeclaredCapability(t *testing.T) {
	b := newBroker(t)
	if err := b.Register(plugins.ExamplePluginID, plugins.ExampleStatusCapability, func(context.Context, Request) (Response, error) {
		return Response{Message: "ready", Mode: "offline"}, nil
	}); err != nil {
		t.Fatal(err)
	}
	response, err := b.Invoke(context.Background(), plugins.ExamplePluginID, plugins.ExampleStatusCapability, Request{})
	if err != nil || response.Message != "ready" {
		t.Fatalf("unexpected response %#v, %v", response, err)
	}
}

func TestBrokerContainsPluginPanic(t *testing.T) {
	b := newBroker(t)
	if err := b.Register(plugins.ExamplePluginID, plugins.ExampleStatusCapability, func(context.Context, Request) (Response, error) {
		panic("boom")
	}); err != nil {
		t.Fatal(err)
	}
	if _, err := b.Invoke(context.Background(), plugins.ExamplePluginID, plugins.ExampleStatusCapability, Request{}); err == nil {
		t.Fatal("expected contained panic error")
	}
}

func TestBrokerHonorsCancelledContext(t *testing.T) {
	b := newBroker(t)
	if err := b.Register(plugins.ExamplePluginID, plugins.ExampleStatusCapability, func(context.Context, Request) (Response, error) {
		return Response{Message: "unexpected"}, nil
	}); err != nil {
		t.Fatal(err)
	}
	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	if _, err := b.Invoke(ctx, plugins.ExamplePluginID, plugins.ExampleStatusCapability, Request{}); !errors.Is(err, context.Canceled) {
		t.Fatalf("expected cancellation, got %v", err)
	}
}
