package server

import (
	"context"
	"encoding/json"
	"io/fs"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"testing/fstest"

	"github.com/wmstipes/The-Foundry-Initiative/apps/forgeops-console/internal/broker"
	"github.com/wmstipes/The-Foundry-Initiative/apps/forgeops-console/internal/config"
	"github.com/wmstipes/The-Foundry-Initiative/apps/forgeops-console/internal/plugins"
	"github.com/wmstipes/The-Foundry-Initiative/apps/forgeops-console/internal/session"
)

const testHost = "127.0.0.1:9090"

func testHandler(t *testing.T) http.Handler {
	t.Helper()
	state, err := session.New([]string{"dev", "prod"})
	if err != nil {
		t.Fatal(err)
	}
	registry, err := plugins.NewRegistry(plugins.ExampleManifest())
	if err != nil {
		t.Fatal(err)
	}
	capabilityBroker, err := broker.New(registry)
	if err != nil {
		t.Fatal(err)
	}
	if err := capabilityBroker.Register(plugins.ExamplePluginID, plugins.ExampleStatusCapability, func(context.Context, broker.Request) (broker.Response, error) {
		return broker.Response{Message: "The example plugin is loaded without cluster access.", Mode: "offline-c2"}, nil
	}); err != nil {
		t.Fatal(err)
	}
	static := fstest.MapFS{
		"index.html": &fstest.MapFile{Data: []byte("<html>shell</html>")},
		"app.js":     &fstest.MapFile{Data: []byte("console.log('local')")},
	}
	handler, err := New(Options{
		AllowedHost: testHost,
		Contexts: []config.ContextSummary{
			{Name: "dev", ClusterName: "dev-cluster", AuthInfoName: "dev-user"},
			{Name: "prod", ClusterName: "prod-cluster", AuthInfoName: "prod-user"},
		},
		State: state, Registry: registry, Broker: capabilityBroker, Static: fs.FS(static), Nonce: "test-nonce",
	})
	if err != nil {
		t.Fatal(err)
	}
	return handler
}

func request(t *testing.T, handler http.Handler, method, target, body string, headers map[string]string) *httptest.ResponseRecorder {
	t.Helper()
	req := httptest.NewRequest(method, target, strings.NewReader(body))
	req.Host = testHost
	for key, value := range headers {
		req.Header.Set(key, value)
	}
	recorder := httptest.NewRecorder()
	handler.ServeHTTP(recorder, req)
	return recorder
}

func TestValidateListenAddressRequiresLiteralLoopback(t *testing.T) {
	for _, valid := range []string{"127.0.0.1:9090", "[::1]:9090"} {
		if err := ValidateListenAddress(valid); err != nil {
			t.Fatalf("expected %q to be valid: %v", valid, err)
		}
	}
	for _, invalid := range []string{"localhost:9090", "0.0.0.0:9090", "10.0.0.1:9090", "127.0.0.1"} {
		if err := ValidateListenAddress(invalid); err == nil {
			t.Fatalf("expected %q to be rejected", invalid)
		}
	}
}

func TestBootstrapIsSanitizedAndStartsUnselected(t *testing.T) {
	response := request(t, testHandler(t), http.MethodGet, "http://"+testHost+"/api/v1/bootstrap", "", nil)
	if response.Code != http.StatusOK {
		t.Fatalf("unexpected status %d", response.Code)
	}
	if strings.Contains(response.Body.String(), "token") || strings.Contains(response.Body.String(), "certificate-authority-data") {
		t.Fatal("bootstrap disclosed credential material")
	}
	var bootstrap bootstrapResponse
	if err := json.Unmarshal(response.Body.Bytes(), &bootstrap); err != nil {
		t.Fatal(err)
	}
	if bootstrap.Mode != "offline-c2" || bootstrap.SelectedContext != "" || bootstrap.SessionNonce != "test-nonce" || len(bootstrap.Plugins) != 1 {
		t.Fatalf("unexpected bootstrap %#v", bootstrap)
	}
}

func TestStateChangesRequireNonceAndKnownContext(t *testing.T) {
	handler := testHandler(t)
	denied := request(t, handler, http.MethodPost, "http://"+testHost+"/api/v1/context", `{"context":"dev"}`, nil)
	if denied.Code != http.StatusForbidden {
		t.Fatalf("expected denial, got %d", denied.Code)
	}
	unknown := request(t, handler, http.MethodPost, "http://"+testHost+"/api/v1/context", `{"context":"missing"}`, map[string]string{"X-ForgeOps-Session": "test-nonce"})
	if unknown.Code != http.StatusBadRequest {
		t.Fatalf("expected invalid context, got %d", unknown.Code)
	}
	selected := request(t, handler, http.MethodPost, "http://"+testHost+"/api/v1/context", `{"context":"dev"}`, map[string]string{"X-ForgeOps-Session": "test-nonce"})
	if selected.Code != http.StatusOK || !strings.Contains(selected.Body.String(), `"dev"`) {
		t.Fatalf("unexpected selection response %d %s", selected.Code, selected.Body.String())
	}
}

func TestStrictRequestParsing(t *testing.T) {
	handler := testHandler(t)
	headers := map[string]string{"X-ForgeOps-Session": "test-nonce"}
	for _, body := range []string{`{"context":"dev","extra":true}`, `{"context":"dev"}{}`, `{`, `{"context":"` + strings.Repeat("x", 5000) + `"}`} {
		response := request(t, handler, http.MethodPost, "http://"+testHost+"/api/v1/context", body, headers)
		if response.Code != http.StatusBadRequest {
			t.Fatalf("expected malformed body rejection, got %d", response.Code)
		}
	}
}

func TestHostAndOriginAreBoundToLoopbackListener(t *testing.T) {
	handler := testHandler(t)
	req := httptest.NewRequest(http.MethodGet, "http://evil.example/api/v1/bootstrap", nil)
	req.Host = "evil.example"
	recorder := httptest.NewRecorder()
	handler.ServeHTTP(recorder, req)
	if recorder.Code != http.StatusForbidden {
		t.Fatalf("expected Host denial, got %d", recorder.Code)
	}
	response := request(t, handler, http.MethodGet, "http://"+testHost+"/api/v1/bootstrap", "", map[string]string{"Origin": "http://evil.example"})
	if response.Code != http.StatusForbidden {
		t.Fatalf("expected Origin denial, got %d", response.Code)
	}
}

func TestExamplePluginCapabilityIsInert(t *testing.T) {
	response := request(t, testHandler(t), http.MethodPost, "http://"+testHost+"/api/v1/plugins/forge.example/status", "", map[string]string{"X-ForgeOps-Session": "test-nonce"})
	if response.Code != http.StatusOK || !strings.Contains(response.Body.String(), "without cluster access") {
		t.Fatalf("unexpected plugin response %d %s", response.Code, response.Body.String())
	}
}

func TestStaticShellAndSecurityHeaders(t *testing.T) {
	response := request(t, testHandler(t), http.MethodGet, "http://"+testHost+"/nested/route", "", nil)
	if response.Code != http.StatusOK || !strings.Contains(response.Body.String(), "shell") {
		t.Fatalf("unexpected shell response %d %s", response.Code, response.Body.String())
	}
	for _, header := range []string{"Content-Security-Policy", "X-Content-Type-Options", "Referrer-Policy", "Cache-Control"} {
		if response.Header().Get(header) == "" {
			t.Fatalf("missing %s", header)
		}
	}
}

func TestKnownRoutesRejectUnsupportedMethods(t *testing.T) {
	response := request(t, testHandler(t), http.MethodDelete, "http://"+testHost+"/api/v1/context", "", nil)
	if response.Code != http.StatusMethodNotAllowed {
		t.Fatalf("expected method rejection, got %d", response.Code)
	}
}
