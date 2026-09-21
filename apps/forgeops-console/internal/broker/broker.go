package broker

import (
	"context"
	"errors"
	"fmt"
	"sync"

	"github.com/wmstipes/The-Foundry-Initiative/apps/forgeops-console/internal/plugins"
)

var ErrDenied = errors.New("capability denied")

type Request struct{}

type Response struct {
	Message string `json:"message"`
	Mode    string `json:"mode"`
}

type Handler func(context.Context, Request) (Response, error)

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
			err = fmt.Errorf("plugin capability panicked: %v", recovered)
		}
	}()
	return handler(ctx, request)
}
