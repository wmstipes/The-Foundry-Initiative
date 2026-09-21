package session

import (
	"context"
	"crypto/rand"
	"encoding/base64"
	"errors"
	"sort"
	"sync"
)

var (
	ErrUnknownContext   = errors.New("unknown context")
	ErrUnknownNamespace = errors.New("unknown namespace")
	ErrStaleScope       = errors.New("stale scope generation")
)

type Scope struct {
	Context    string `json:"context"`
	Namespace  string `json:"namespace"`
	Generation uint64 `json:"generation"`
}

type State struct {
	mu                sync.RWMutex
	allowedContexts   map[string]struct{}
	allowedNamespaces map[string]struct{}
	scope             Scope
	scopeContext      context.Context
	cancelScope       context.CancelFunc
}

func New(contextNames []string) (*State, error) {
	allowed := make(map[string]struct{}, len(contextNames))
	for _, name := range contextNames {
		if name == "" {
			return nil, errors.New("context name must not be empty")
		}
		if _, exists := allowed[name]; exists {
			return nil, errors.New("context names must be unique")
		}
		allowed[name] = struct{}{}
	}
	if len(allowed) == 0 {
		return nil, errors.New("at least one context is required")
	}
	return &State{allowedContexts: allowed, allowedNamespaces: make(map[string]struct{})}, nil
}

func (s *State) Select(name string) error {
	_, err := s.SelectContext(name)
	return err
}

func (s *State) SelectContext(name string) (Scope, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	if _, ok := s.allowedContexts[name]; !ok {
		return Scope{}, ErrUnknownContext
	}
	s.advanceLocked()
	s.scope.Context = name
	s.scope.Namespace = ""
	s.allowedNamespaces = make(map[string]struct{})
	return s.scope, nil
}

func (s *State) AllowNamespaces(generation uint64, names []string) error {
	s.mu.Lock()
	defer s.mu.Unlock()
	if generation != s.scope.Generation || s.scope.Context == "" {
		return ErrStaleScope
	}
	allowed := make(map[string]struct{}, len(names))
	for _, name := range names {
		if name != "" {
			allowed[name] = struct{}{}
		}
	}
	s.allowedNamespaces = allowed
	return nil
}

func (s *State) SelectNamespace(name string) (Scope, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	if _, ok := s.allowedNamespaces[name]; !ok {
		return Scope{}, ErrUnknownNamespace
	}
	s.advanceLocked()
	s.scope.Namespace = name
	return s.scope, nil
}

func (s *State) advanceLocked() {
	if s.cancelScope != nil {
		s.cancelScope()
	}
	s.scope.Generation++
	s.scopeContext, s.cancelScope = context.WithCancel(context.Background())
}

func (s *State) RequestContext(parent context.Context, generation uint64) (context.Context, context.CancelFunc, Scope, error) {
	s.mu.RLock()
	defer s.mu.RUnlock()
	if generation == 0 || generation != s.scope.Generation || s.scope.Context == "" || s.scopeContext == nil {
		return nil, nil, Scope{}, ErrStaleScope
	}
	requestContext, cancel := context.WithCancel(parent)
	scopeContext := s.scopeContext
	go func() {
		select {
		case <-scopeContext.Done():
			cancel()
		case <-requestContext.Done():
		}
	}()
	return requestContext, cancel, s.scope, nil
}

func (s *State) Current() Scope {
	s.mu.RLock()
	defer s.mu.RUnlock()
	return s.scope
}

func (s *State) Selected() string { return s.Current().Context }

func (s *State) ContextNames() []string {
	s.mu.RLock()
	defer s.mu.RUnlock()
	names := make([]string, 0, len(s.allowedContexts))
	for name := range s.allowedContexts {
		names = append(names, name)
	}
	sort.Strings(names)
	return names
}

func NewNonce() (string, error) {
	buffer := make([]byte, 32)
	if _, err := rand.Read(buffer); err != nil {
		return "", err
	}
	return base64.RawURLEncoding.EncodeToString(buffer), nil
}
