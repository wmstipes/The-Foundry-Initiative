package broker

import (
	"context"
	"errors"
	"sync"

	"github.com/wmstipes/The-Foundry-Initiative/apps/forgeops-console/internal/diagnostics"
	"github.com/wmstipes/The-Foundry-Initiative/apps/forgeops-console/internal/plugins"
	"github.com/wmstipes/The-Foundry-Initiative/apps/forgeops-console/internal/resources"
)

var ErrDenied = errors.New("capability denied")
var ErrInternal = errors.New("internal capability failure")

type Request struct {
	Query      *resources.Query
	Diagnostic *diagnostics.Query
}

type Response struct {
	Message    string              `json:"message,omitempty"`
	Mode       string              `json:"mode,omitempty"`
	Result     *resources.Result   `json:"result,omitempty"`
	Diagnostic *diagnostics.Result `json:"diagnostic,omitempty"`
}

type Handler func(context.Context, Request) (Response, error)

func (b *Broker) RegisterDiagnostics(service *diagnostics.Service) error {
	for operation, capability := range map[string]string{"logs": "pods.logs.read", "events": "events.read", "preview": "command.preview"} {
		if err := b.Register(plugins.DiagnosticsPluginID, capability, func(ctx context.Context, request Request) (Response, error) {
			if request.Diagnostic == nil || request.Diagnostic.Operation != operation {
				return Response{}, ErrDenied
			}
			result, err := service.Execute(ctx, *request.Diagnostic)
			if err != nil {
				return Response{}, err
			}
			return Response{Diagnostic: &result}, nil
		}); err != nil {
			return err
		}
	}
	return nil
}

type Broker struct {
	mu       sync.RWMutex
	registry *plugins.Registry
	handlers map[string]map[string]Handler
}

func New(registry *plugins.Registry) (*Broker, error) {
	if registry == nil {
		return nil, errors.New("plugin registry is required")
	}
	return &Broker{registry: registry, handlers: make(map[string]map[string]Handler)}, nil
}

func (b *Broker) Register(pluginID, capability string, handler Handler) error {
	manifest, ok := b.registry.Get(pluginID)
	if !ok || !manifest.Declares(capability) || handler == nil {
		return ErrDenied
	}
	b.mu.Lock()
	defer b.mu.Unlock()
	if b.handlers[pluginID] == nil {
		b.handlers[pluginID] = make(map[string]Handler)
	}
	if _, exists := b.handlers[pluginID][capability]; exists {
		return errors.New("capability handler already registered")
	}
	b.handlers[pluginID][capability] = handler
	return nil
}

func (b *Broker) Invoke(ctx context.Context, pluginID, capability string, request Request) (response Response, err error) {
	manifest, ok := b.registry.Get(pluginID)
	if !ok || !manifest.Declares(capability) {
		return Response{}, ErrDenied
	}
	b.mu.RLock()
	handler := b.handlers[pluginID][capability]
	b.mu.RUnlock()
	if handler == nil {
		return Response{}, ErrDenied
	}
	if err := ctx.Err(); err != nil {
		return Response{}, err
	}
	defer func() {
		if recovered := recover(); recovered != nil {
			response = Response{}
			err = ErrInternal
		}
	}()
	return handler(ctx, request)
}

// ValidateComplete is called after startup registration, before serving requests.
func (b *Broker) ValidateComplete() error {
	b.mu.RLock()
	defer b.mu.RUnlock()
	for _, manifest := range b.registry.Manifests() {
		for _, capability := range manifest.Capabilities {
			if b.handlers[manifest.ID][capability] == nil {
				return errors.New("compiled capability handler missing")
			}
		}
	}
	return nil
}
