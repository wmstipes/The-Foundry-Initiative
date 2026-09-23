package main

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"testing"

	discoveryv1 "k8s.io/api/discovery/v1"
	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/kubernetes/fake"
	clientcmdapi "k8s.io/client-go/tools/clientcmd/api"

	"github.com/wmstipes/The-Foundry-Initiative/apps/forgeops-console/internal/cluster"
	"github.com/wmstipes/The-Foundry-Initiative/apps/forgeops-console/internal/resources"
	"github.com/wmstipes/The-Foundry-Initiative/apps/forgeops-console/internal/session"
)

func TestRoutingScenariosMatchReviewedFixtureAndProjection(t *testing.T) {
	for _, stage := range []struct{ scenario, fixture, status string }{
		{"routing-before", "before.json", "3/3 ready"},
		{"routing-after", "after.json", "2/3 ready"},
	} {
		t.Run(stage.scenario, func(t *testing.T) {
			contextName, objects, err := scenarioObjects(stage.scenario)
			if err != nil {
				t.Fatal(err)
			}
			if contextName == "kubernetes-admin@kubernetes" {
				t.Fatal("demo context must not impersonate the snapshot's context")
			}
			var slices []*discoveryv1.EndpointSlice
			for _, object := range objects {
				if slice, ok := object.(*discoveryv1.EndpointSlice); ok {
					slices = append(slices, slice)
				}
			}
			if len(slices) != 1 || slices[0].Namespace != "forge-restaurant" || slices[0].Labels[discoveryv1.LabelServiceName] != "synthetic-service" {
				t.Fatalf("unexpected synthetic routing identity: %#v", slices)
			}
			ready, notReady, unknown := 0, 0, 0
			for _, endpoint := range slices[0].Endpoints {
				switch {
				case endpoint.Conditions.Ready == nil:
					unknown++
				case *endpoint.Conditions.Ready:
					ready++
				default:
					notReady++
				}
			}
			var fixture struct {
				Checks []struct {
					ID       string `json:"id"`
					Observed string `json:"observed"`
				} `json:"checks"`
			}
			path := filepath.Join("..", "..", "..", "..", "tests", "fixtures", "forgeops", "scenarios", "routing-regression", stage.fixture)
			data, err := os.ReadFile(path)
			if err != nil {
				t.Fatal(err)
			}
			if err := json.Unmarshal(data, &fixture); err != nil {
				t.Fatal(err)
			}
			observed := fmt.Sprintf("slices=%d, ready=%d, notReady=%d, unknown=%d", len(slices), ready, notReady, unknown)
			if len(fixture.Checks) != 1 || fixture.Checks[0].ID != "routing.forge-restaurant.synthetic-service" || fixture.Checks[0].Observed != observed {
				t.Fatalf("Console synthetic data %q does not align with reviewed fixture: %#v", observed, fixture.Checks)
			}
			state, err := session.New([]string{contextName})
			if err != nil {
				t.Fatal(err)
			}
			scope, err := state.SelectContext(contextName)
			if err != nil {
				t.Fatal(err)
			}
			if err := state.AllowNamespaces(scope.Generation, []string{"forge-restaurant"}); err != nil {
				t.Fatal(err)
			}
			scope, err = state.SelectNamespace("forge-restaurant")
			if err != nil {
				t.Fatal(err)
			}
			client := fake.NewSimpleClientset(objects...)
			factory := cluster.ClientFactoryFunc(func(context.Context, *clientcmdapi.Config, string) (kubernetes.Interface, error) { return client, nil })
			service, err := resources.New(demoConfig(contextName), state, factory)
			if err != nil {
				t.Fatal(err)
			}
			result, err := service.Execute(context.Background(), resources.Query{Generation: scope.Generation, Operation: "list", Resource: "endpointslices"})
			if err != nil {
				t.Fatal(err)
			}
			if result.Truncated || len(result.Items) != 1 || result.Items[0].Status != stage.status || result.Items[0].Name != "synthetic-service-demo" {
				t.Fatalf("unexpected projected EndpointSlice: %#v", result)
			}
			services, err := service.Execute(context.Background(), resources.Query{Generation: scope.Generation, Operation: "list", Resource: "services"})
			if err != nil {
				t.Fatal(err)
			}
			if services.Truncated || len(services.Items) != 1 || services.Items[0].Name != "synthetic-service" {
				t.Fatalf("unexpected projected Service: %#v", services)
			}
			linked := false
			for _, relation := range services.Items[0].Related {
				if relation.Kind == "EndpointSlice" && relation.Name == "synthetic-service-demo" && relation.Relation == "routes-via" {
					linked = true
				}
			}
			if !linked {
				t.Fatalf("Service does not link to the reviewed slice: %#v", services.Items[0].Related)
			}
		})
	}
}

func TestUnknownScenarioIsRejected(t *testing.T) {
	if _, _, err := scenarioObjects("live"); err == nil {
		t.Fatal("unknown scenario accepted")
	}
}
