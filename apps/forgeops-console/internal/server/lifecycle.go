package server

import (
	"context"
	"errors"
	"net"
	"net/http"
	"time"

	"github.com/wmstipes/The-Foundry-Initiative/apps/forgeops-console/internal/session"
)

// ListenAndServe joins graceful shutdown before returning. Handler cancellation
// remains cooperative; on deadline Close bounds transport cleanup, not Go code.
func ListenAndServe(ctx context.Context, httpServer *http.Server, state *session.State) error {
	if err := ValidateListenAddress(httpServer.Addr); err != nil {
		return err
	}
	listener, err := net.Listen("tcp", httpServer.Addr)
	if err != nil {
		state.Close()
		return err
	}
	return serve(ctx, httpServer, listener, state, 5*time.Second)
}

func serve(ctx context.Context, httpServer *http.Server, listener net.Listener, state *session.State, timeout time.Duration) error {
	defer state.Close()
	done := make(chan error, 1)
	go func() { done <- httpServer.Serve(listener) }()
	select {
	case err := <-done:
		if errors.Is(err, http.ErrServerClosed) {
			return nil
		}
		return err
	case <-ctx.Done():
		state.Close()
		drain, cancel := context.WithTimeout(context.Background(), timeout)
		defer cancel()
		err := httpServer.Shutdown(drain)
		if err != nil {
			_ = httpServer.Close()
		}
		serveErr := <-done
		if err != nil {
			return err
		}
		if !errors.Is(serveErr, http.ErrServerClosed) {
			return serveErr
		}
		return nil
	}
}
