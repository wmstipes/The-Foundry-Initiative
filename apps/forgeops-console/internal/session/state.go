package session

import (
	"crypto/rand"
	"encoding/base64"
	"errors"
	"sort"
	"sync"
)

var ErrUnknownContext = errors.New("unknown context")

type State struct {
	mu       sync.RWMutex
	allowed  map[string]struct{}
	selected string
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
	return &State{allowed: allowed}, nil
}

func (s *State) Select(name string) error {
	s.mu.Lock()
	defer s.mu.Unlock()
	if _, ok := s.allowed[name]; !ok {
		return ErrUnknownContext
	}
	s.selected = name
	return nil
}

func (s *State) Selected() string {
	s.mu.RLock()
	defer s.mu.RUnlock()
	return s.selected
}

func (s *State) ContextNames() []string {
	s.mu.RLock()
	defer s.mu.RUnlock()
	names := make([]string, 0, len(s.allowed))
	for name := range s.allowed {
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
