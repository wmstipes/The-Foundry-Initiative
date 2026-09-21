package server

import (
	"context"
	"encoding/json"
	"errors"
	"io/fs"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"testing/fstest"

	corev1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/kubernetes/fake"
	clientcmdapi "k8s.io/client-go/tools/clientcmd/api"

	"github.com/wmstipes/The-Foundry-Initiative/apps/forgeops-console/internal/broker"
	"github.com/wmstipes/The-Foundry-Initiative/apps/forgeops-console/internal/cluster"
	"github.com/wmstipes/The-Foundry-Initiative/apps/forgeops-console/internal/config"
	"github.com/wmstipes/The-Foundry-Initiative/apps/forgeops-console/internal/diagnostics"
	"github.com/wmstipes/The-Foundry-Initiative/apps/forgeops-console/internal/plugins"
	"github.com/wmstipes/The-Foundry-Initiative/apps/forgeops-console/internal/resources"
	"github.com/wmstipes/The-Foundry-Initiative/apps/forgeops-console/internal/session"
)

const testHost = "127.0.0.1:9090"

func testHandler(t *testing.T) http.Handler {
	t.Helper()
	state, err := session.New([]string{"dev", "prod"})
	if err != nil {
		t.Fatal(err)
	}
	registry, err := plugins.NewRegistry(plugins.ExampleManifest(), plugins.ResourcesManifest(), plugins.DiagnosticsManifest())
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
	raw := &clientcmdapi.Config{Contexts: map[string]*clientcmdapi.Context{"dev": {Cluster: "dev", AuthInfo: "user"}, "prod": {Cluster: "prod", AuthInfo: "user"}}}
	fakeClient := fake.NewSimpleClientset(&corev1.Namespace{ObjectMeta: metav1.ObjectMeta{Name: "default"}, Status: corev1.NamespaceStatus{Phase: corev1.NamespaceActive}})
	resourceService, err := resources.New(raw, state, cluster.ClientFactoryFunc(func(context.Context, *clientcmdapi.Config, string) (kubernetes.Interface, error) {
		return fakeClient, nil
	}))
	if err != nil {
		t.Fatal(err)
	}
	if err := capabilityBroker.Register(plugins.ResourcesPluginID, plugins.ResourcesReadCapability, func(ctx context.Context, request broker.Request) (broker.Response, error) {
		if request.Query == nil {
			return broker.Response{}, errors.New("missing query")
		}
		result, err := resourceService.Execute(ctx, *request.Query)
		if err != nil {
			return broker.Response{}, err
		}
		return broker.Response{Result: &result}, nil
	}); err != nil {
		t.Fatal(err)
	}
	diagnosticService, err := diagnostics.New(raw, state, cluster.OfflineFactory{}, nil, resourceService.RecordDiagnostic)
	if err != nil {
		t.Fatal(err)
	}
	if err = capabilityBroker.RegisterDiagnostics(diagnosticService); err != nil {
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
		State: state, Registry: registry, Broker: capabilityBroker, Resources: resourceService, Static: fs.FS(static), Nonce: "test-nonce", Mode: "synthetic-demo",
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
	if bootstrap.Mode != "synthetic-demo" || bootstrap.SelectedContext != "" || bootstrap.SessionNonce != "test-nonce" || len(bootstrap.Plugins) != 3 {
		t.Fatalf("unexpected bootstrap %#v", bootstrap)
	}
}

func TestDiagnosticRouteSecurityAndStrictShape(t *testing.T) {
	handler := testHandler(t)
	endpoint := "http://" + testHost + "/api/v1/plugins/forge.diagnostics/query"
	body := `{"generation":2,"operation":"logs","pod":"api","container":"api"}`
	headers := map[string]string{"X-ForgeOps-Session": "test-nonce"}
	if got := request(t, handler, http.MethodPost, endpoint, body, nil); got.Code != 403 {
		t.Fatalf("nonce %d", got.Code)
	}
	for _, payload := range []string{`{"operation":"exec"}`, `{"operation":"logs","pod":"api","command":"evil"}`, body + `{}`, strings.Repeat("x", 5000)} {
		if got := request(t, handler, http.MethodPost, endpoint, payload, headers); got.Code != 400 {
			t.Fatalf("strict decode %d", got.Code)
		}
	}
	if got := request(t, handler, http.MethodPost, endpoint+"?pod=api", body, headers); got.Code != 400 {
		t.Fatalf("URL data %d", got.Code)
	}
	if got := request(t, handler, http.MethodPost, endpoint, body, map[string]string{"X-ForgeOps-Session": "test-nonce", "Origin": "http://evil.example"}); got.Code != 403 {
		t.Fatalf("origin %d", got.Code)
	}
	if got := request(t, handler, http.MethodGet, endpoint, "", headers); got.Code != 404 && got.Code != 405 {
		t.Fatalf("method %d", got.Code)
	}
	if got := request(t, handler, http.MethodPost, endpoint, body, headers); got.Code != 409 {
		t.Fatalf("stale %d", got.Code)
	}
}

func TestDiagnosticPreviewRouteIsOfflineAndNoStore(t *testing.T) {
	handler := testHandler(t)
	headers := map[string]string{"X-ForgeOps-Session": "test-nonce"}
	request(t, handler, "POST", "http://"+testHost+"/api/v1/context", `{"context":"dev"}`, headers)
	request(t, handler, "POST", "http://"+testHost+"/api/v1/plugins/forge.resources/query", `{"generation":1,"operation":"list","resource":"namespaces"}`, headers)
	request(t, handler, "POST", "http://"+testHost+"/api/v1/namespace", `{"generation":1,"namespace":"default"}`, headers)
	got := request(t, handler, "POST", "http://"+testHost+"/api/v1/plugins/forge.diagnostics/query", `{"generation":2,"operation":"preview","target":"events","pod":"api"}`, headers)
	if got.Code != 200 || !strings.Contains(got.Body.String(), "Explanation only") || got.Header().Get("Cache-Control") != "no-store" {
		t.Fatalf("preview %d %s", got.Code, got.Body.String())
	}
	got = request(t, handler, "POST", "http://"+testHost+"/api/v1/plugins/forge.diagnostics/query", `{"generation":2,"operation":"events","pod":"api"}`, headers)
	if got.Code != 503 || strings.Contains(got.Body.String(), "offline mode") {
		t.Fatalf("upstream detail %d %s", got.Code, got.Body.String())
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

func TestResourceQueryRequiresCurrentScopeAndExplicitNamespace(t *testing.T) {
	handler := testHandler(t)
	headers := map[string]string{"X-ForgeOps-Session": "test-nonce", "Content-Type": "application/json"}
	selected := request(t, handler, http.MethodPost, "http://"+testHost+"/api/v1/context", `{"context":"dev"}`, headers)
	if selected.Code != http.StatusOK {
		t.Fatalf("select context: %d %s", selected.Code, selected.Body.String())
	}
	namespaces := request(t, handler, http.MethodPost, "http://"+testHost+"/api/v1/plugins/forge.resources/query", `{"generation":1,"operation":"list","resource":"namespaces"}`, headers)
	if namespaces.Code != http.StatusOK || !strings.Contains(namespaces.Body.String(), `"default"`) {
		t.Fatalf("list namespaces: %d %s", namespaces.Code, namespaces.Body.String())
	}
	namespace := request(t, handler, http.MethodPost, "http://"+testHost+"/api/v1/namespace", `{"namespace":"default","generation":1}`, headers)
	if namespace.Code != http.StatusOK || !strings.Contains(namespace.Body.String(), `"generation":2`) {
		t.Fatalf("select namespace: %d %s", namespace.Code, namespace.Body.String())
	}
	stale := request(t, handler, http.MethodPost, "http://"+testHost+"/api/v1/plugins/forge.resources/query", `{"generation":1,"operation":"list","resource":"pods"}`, headers)
	if stale.Code != http.StatusConflict || !strings.Contains(stale.Body.String(), "stale_scope") {
		t.Fatalf("stale request: %d %s", stale.Code, stale.Body.String())
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
