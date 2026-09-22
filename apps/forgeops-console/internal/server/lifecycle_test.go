package server

import (
	"context"
	"errors"
	"net"
	"net/http"
	"testing"
	"time"

	"github.com/wmstipes/The-Foundry-Initiative/apps/forgeops-console/internal/session"
)

func TestShutdownJoinsDrainAndBoundsUncooperativeHandler(t *testing.T) {
	for _, mode := range []string{"drain", "deadline"} {
		t.Run(mode, func(t *testing.T) {
			state, _ := session.New([]string{"dev"})
			scope, _ := state.SelectContext("dev")
			started := make(chan context.Context, 1)
			release := make(chan struct{})
			finished := make(chan struct{})
			released := false
			defer func() {
				if !released {
					close(release)
				}
				select {
				case <-finished:
				case <-time.After(time.Second):
					t.Error("handler did not exit")
				}
			}()
			httpServer := &http.Server{Handler: http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				defer close(finished)
				request, cancel, _, err := state.RequestContext(r.Context(), scope.Generation)
				if err != nil {
					t.Error(err)
					return
				}
				defer cancel()
				started <- request
				<-release // Deliberately ignore cancellation until the test releases this gate.
				w.WriteHeader(http.StatusNoContent)
			})}
			listener, err := net.Listen("tcp", "127.0.0.1:0")
			if err != nil {
				t.Fatal(err)
			}
			ctx, cancel := context.WithCancel(context.Background())
			defer cancel()
			done := make(chan error, 1)
			timeout := time.Second
			if mode == "deadline" {
				timeout = 30 * time.Millisecond
			}
			go func() { done <- serve(ctx, httpServer, listener, state, timeout) }()
			go func() {
				response, err := http.Get("http://" + listener.Addr().String())
				if err == nil {
					response.Body.Close()
				}
			}()
			var request context.Context
			select {
			case request = <-started:
			case <-time.After(2 * time.Second):
				t.Fatal("request did not start")
			}
			cancel()
			select {
			case <-request.Done():
			case <-time.After(time.Second):
				t.Fatal("session was not cancelled")
			}
			if mode == "drain" {
				select {
				case err := <-done:
					t.Fatalf("returned before drain: %v", err)
				default:
				}
				close(release)
				released = true
			}
			select {
			case err := <-done:
				if mode == "drain" && err != nil {
					t.Fatal(err)
				}
				if mode == "deadline" && !errors.Is(err, context.DeadlineExceeded) {
					t.Fatalf("deadline not reported: %v", err)
				}
			case <-time.After(2 * time.Second):
				t.Fatal("shutdown hung")
			}
		})
	}
}
