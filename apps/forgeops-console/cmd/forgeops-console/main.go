package main

import (
	"context"
	"errors"
	"flag"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/wmstipes/The-Foundry-Initiative/apps/forgeops-console/internal/broker"
	"github.com/wmstipes/The-Foundry-Initiative/apps/forgeops-console/internal/cluster"
	"github.com/wmstipes/The-Foundry-Initiative/apps/forgeops-console/internal/config"
	"github.com/wmstipes/The-Foundry-Initiative/apps/forgeops-console/internal/plugins"
	"github.com/wmstipes/The-Foundry-Initiative/apps/forgeops-console/internal/resources"
	"github.com/wmstipes/The-Foundry-Initiative/apps/forgeops-console/internal/server"
	"github.com/wmstipes/The-Foundry-Initiative/apps/forgeops-console/internal/session"
)

func main() {
	if err := run(); err != nil {
		log.Printf("ForgeOps Console stopped: %v", err)
		os.Exit(1)
	}
}

func run() error {
	kubeconfigPath := flag.String("kubeconfig", "", "path to the explicit kubeconfig fixture")
	listenAddress := flag.String("listen", "127.0.0.1:9090", "literal loopback listen address")
	webDirectory := flag.String("web-dir", "", "path to the built browser assets")
	flag.Parse()

	if *webDirectory == "" {
		return errors.New("--web-dir is required")
	}
	if err := server.ValidateListenAddress(*listenAddress); err != nil {
		return err
	}
	loaded, err := config.LoadExplicit(*kubeconfigPath)
	if err != nil {
		return err
	}
	contextNames := make([]string, 0, len(loaded.Contexts))
	for _, summary := range loaded.Contexts {
		contextNames = append(contextNames, summary.Name)
	}
	state, err := session.New(contextNames)
	if err != nil {
		return err
	}
	nonce, err := session.NewNonce()
	if err != nil {
		return fmt.Errorf("create session nonce: %w", err)
	}
	registry, err := plugins.NewRegistry(plugins.ExampleManifest(), plugins.ResourcesManifest())
	if err != nil {
		return err
	}
	capabilityBroker, err := broker.New(registry)
	if err != nil {
		return err
	}
	if err := capabilityBroker.Register(plugins.ExamplePluginID, plugins.ExampleStatusCapability, func(context.Context, broker.Request) (broker.Response, error) {
		return broker.Response{Message: "The example plugin has no cluster capability.", Mode: "read-only-c3"}, nil
	}); err != nil {
		return err
	}
	resourceService, err := resources.New(loaded.Config, state, cluster.LiveFactory{})
	if err != nil {
		return err
	}
	if err := capabilityBroker.Register(plugins.ResourcesPluginID, plugins.ResourcesReadCapability, func(ctx context.Context, request broker.Request) (broker.Response, error) {
		if request.Query == nil {
			return broker.Response{}, &resources.APIError{Code: "invalid_request", Status: http.StatusBadRequest}
		}
		result, err := resourceService.Execute(ctx, *request.Query)
		if err != nil {
			return broker.Response{}, err
		}
		return broker.Response{Result: &result}, nil
	}); err != nil {
		return err
	}
	handler, err := server.New(server.Options{
		AllowedHost: *listenAddress,
		Contexts:    loaded.Contexts,
		State:       state,
		Registry:    registry,
		Broker:      capabilityBroker,
		Resources:   resourceService,
		Static:      os.DirFS(*webDirectory),
		Nonce:       nonce,
		Mode:        "read-only-c3",
	})
	if err != nil {
		return err
	}

	httpServer := &http.Server{
		Addr:              *listenAddress,
		Handler:           handler,
		ReadHeaderTimeout: 5 * time.Second,
		ReadTimeout:       10 * time.Second,
		WriteTimeout:      15 * time.Second,
		IdleTimeout:       30 * time.Second,
	}
	shutdownContext, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()
	go func() {
		<-shutdownContext.Done()
		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()
		_ = httpServer.Shutdown(ctx)
	}()

	log.Printf("ForgeOps Console C3 listening at http://%s (read-only mode)", *listenAddress)
	if err := httpServer.ListenAndServe(); err != nil && !errors.Is(err, http.ErrServerClosed) {
		return err
	}
	return nil
}
