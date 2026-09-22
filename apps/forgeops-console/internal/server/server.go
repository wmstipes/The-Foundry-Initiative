package server

import (
	"bytes"
	"context"
	"crypto/subtle"
	"encoding/json"
	"errors"
	"io"
	"io/fs"
	"mime"
	"net"
	"net/http"
	"net/url"
	"path"
	"strings"

	console "github.com/wmstipes/The-Foundry-Initiative/apps/forgeops-console"
	"github.com/wmstipes/The-Foundry-Initiative/apps/forgeops-console/internal/broker"
	"github.com/wmstipes/The-Foundry-Initiative/apps/forgeops-console/internal/config"
	"github.com/wmstipes/The-Foundry-Initiative/apps/forgeops-console/internal/diagnostics"
	"github.com/wmstipes/The-Foundry-Initiative/apps/forgeops-console/internal/plugins"
	"github.com/wmstipes/The-Foundry-Initiative/apps/forgeops-console/internal/resources"
	"github.com/wmstipes/The-Foundry-Initiative/apps/forgeops-console/internal/session"
)

const maxRequestBytes int64 = 4 << 10

type Options struct {
	AllowedHost string
	Contexts    []config.ContextSummary
	State       *session.State
	Registry    *plugins.Registry
	Broker      *broker.Broker
	Resources   *resources.Service
	Static      fs.FS
	Nonce       string
	Mode        string
}

type api struct {
	options Options
}

type bootstrapResponse struct {
	Bundle          console.BundleIdentity  `json:"bundle"`
	Mode            string                  `json:"mode"`
	SessionNonce    string                  `json:"sessionNonce"`
	SelectedContext string                  `json:"selectedContext"`
	Scope           session.Scope           `json:"scope"`
	Contexts        []config.ContextSummary `json:"contexts"`
	Plugins         []plugins.Manifest      `json:"plugins"`
}

func ValidateListenAddress(address string) error {
	host, _, err := net.SplitHostPort(address)
	if err != nil {
		return errors.New("listen address must include a literal IP address and port")
	}
	ip := net.ParseIP(host)
	if ip == nil || !ip.IsLoopback() {
		return errors.New("listen address must use a literal loopback IP")
	}
	return nil
}

func New(options Options) (http.Handler, error) {
	if err := ValidateListenAddress(options.AllowedHost); err != nil {
		return nil, err
	}
	if options.State == nil || options.Registry == nil || options.Broker == nil || options.Resources == nil || options.Static == nil || options.Nonce == "" || options.Mode == "" {
		return nil, errors.New("server options are incomplete")
	}
	if err := validateBundle(options.Static); err != nil {
		return nil, err
	}
	if err := options.Broker.ValidateComplete(); err != nil {
		return nil, err
	}
	application := &api{options: options}
	mux := http.NewServeMux()
	mux.HandleFunc("GET /healthz", application.health)
	mux.HandleFunc("GET /api/v1/bootstrap", application.bootstrap)
	mux.HandleFunc("POST /api/v1/context", application.selectContext)
	mux.HandleFunc("POST /api/v1/namespace", application.selectNamespace)
	mux.HandleFunc("POST /api/v1/plugins/forge.example/status", application.exampleStatus)
	mux.HandleFunc("POST /api/v1/plugins/forge.resources/query", application.resourceQuery)
	mux.HandleFunc("POST /api/v1/activity", application.activity)
	mux.HandleFunc("POST /api/v1/plugins/forge.diagnostics/query", application.diagnosticQuery)
	mux.HandleFunc("/", application.static)
	return application.security(mux), nil
}

func (a *api) security(next http.Handler) http.Handler {
	return http.HandlerFunc(func(writer http.ResponseWriter, request *http.Request) {
		writer.Header().Set("Cache-Control", "no-store")
		writer.Header().Set("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'none'")
		writer.Header().Set("Referrer-Policy", "no-referrer")
		writer.Header().Set("X-Content-Type-Options", "nosniff")
		if request.Host != a.options.AllowedHost || !a.validOrigin(request.Header.Get("Origin")) {
			http.Error(writer, "request origin denied", http.StatusForbidden)
			return
		}
		next.ServeHTTP(writer, request)
	})
}

func (a *api) validOrigin(raw string) bool {
	if raw == "" {
		return true
	}
	origin, err := url.Parse(raw)
	return err == nil && origin.Scheme == "http" && origin.Host == a.options.AllowedHost && origin.User == nil && origin.Opaque == "" && origin.Path == "" && origin.RawQuery == "" && origin.Fragment == ""
}

func (a *api) health(writer http.ResponseWriter, _ *http.Request) {
	writeJSON(writer, http.StatusOK, map[string]string{"status": "ok", "mode": a.options.Mode})
}

func (a *api) bootstrap(writer http.ResponseWriter, _ *http.Request) {
	writeJSON(writer, http.StatusOK, bootstrapResponse{
		Bundle:          console.Bundle(),
		Mode:            a.options.Mode,
		SessionNonce:    a.options.Nonce,
		SelectedContext: a.options.State.Selected(),
		Scope:           a.options.State.Current(),
		Contexts:        a.options.Contexts,
		Plugins:         a.options.Registry.Manifests(),
	})
}

func (a *api) selectContext(writer http.ResponseWriter, request *http.Request) {
	if !a.validNonce(request) {
		http.Error(writer, "session denied", http.StatusForbidden)
		return
	}
	var input struct {
		Context string `json:"context"`
	}
	if err := decodeJSON(writer, request, &input); err != nil {
		return
	}
	scope, err := a.options.State.SelectContext(input.Context)
	if err != nil {
		writeJSON(writer, http.StatusBadRequest, map[string]string{"error": "unknown context"})
		return
	}
	writeJSON(writer, http.StatusOK, scope)
}

func (a *api) selectNamespace(writer http.ResponseWriter, request *http.Request) {
	if !a.validNonce(request) {
		http.Error(writer, "session denied", http.StatusForbidden)
		return
	}
	var input struct {
		Namespace  string `json:"namespace"`
		Generation uint64 `json:"generation"`
	}
	if err := decodeJSON(writer, request, &input); err != nil {
		return
	}
	scope, err := a.options.State.SelectNamespaceAt(input.Namespace, input.Generation)
	if errors.Is(err, session.ErrStaleScope) {
		writeJSON(writer, http.StatusConflict, map[string]string{"error": "stale_scope"})
		return
	}
	if err != nil {
		writeJSON(writer, http.StatusBadRequest, map[string]string{"error": "unknown_namespace"})
		return
	}
	writeJSON(writer, http.StatusOK, scope)
}

func (a *api) exampleStatus(writer http.ResponseWriter, request *http.Request) {
	if !a.validNonce(request) {
		http.Error(writer, "session denied", http.StatusForbidden)
		return
	}
	response, err := a.options.Broker.Invoke(request.Context(), plugins.ExamplePluginID, plugins.ExampleStatusCapability, broker.Request{})
	if err != nil {
		writeBrokerError(writer, err)
		return
	}
	writeJSON(writer, http.StatusOK, response)
}

func (a *api) resourceQuery(writer http.ResponseWriter, request *http.Request) {
	if !a.validNonce(request) {
		http.Error(writer, "session denied", http.StatusForbidden)
		return
	}
	var query resources.Query
	if err := decodeJSON(writer, request, &query); err != nil {
		return
	}
	response, err := a.options.Broker.Invoke(request.Context(), plugins.ResourcesPluginID, plugins.ResourcesReadCapability, broker.Request{Query: &query})
	if err != nil {
		var apiError *resources.APIError
		if errors.As(err, &apiError) {
			writeJSON(writer, apiError.Status, map[string]string{"error": apiError.Code})
			return
		}
		writeBrokerError(writer, err)
		return
	}
	writeJSON(writer, http.StatusOK, response.Result)
}

func (a *api) activity(writer http.ResponseWriter, request *http.Request) {
	if !a.validNonce(request) {
		http.Error(writer, "session denied", http.StatusForbidden)
		return
	}
	writeJSON(writer, http.StatusOK, map[string]any{"activity": a.options.Resources.Activity()})
}

func (a *api) diagnosticQuery(writer http.ResponseWriter, request *http.Request) {
	if !a.validNonce(request) {
		http.Error(writer, "session denied", http.StatusForbidden)
		return
	}
	if request.URL.RawQuery != "" {
		writeJSON(writer, 400, map[string]string{"error": "invalid_request"})
		return
	}
	var query diagnostics.Query
	if decodeJSON(writer, request, &query) != nil {
		return
	}
	capability, ok := map[string]string{"logs": "pods.logs.read", "events": "events.read", "preview": "command.preview"}[query.Operation]
	if !ok {
		writeJSON(writer, 400, map[string]string{"error": "invalid_request"})
		return
	}
	response, err := a.options.Broker.Invoke(request.Context(), plugins.DiagnosticsPluginID, capability, broker.Request{Diagnostic: &query})
	if err != nil {
		var mapped *resources.APIError
		if errors.As(err, &mapped) {
			writeJSON(writer, mapped.Status, map[string]string{"error": mapped.Code})
			return
		}
		writeBrokerError(writer, err)
		return
	}
	writeJSON(writer, 200, response.Diagnostic)
}

func (a *api) validNonce(request *http.Request) bool {
	provided := request.Header.Get("X-ForgeOps-Session")
	return len(provided) == len(a.options.Nonce) && subtle.ConstantTimeCompare([]byte(provided), []byte(a.options.Nonce)) == 1
}

func (a *api) static(writer http.ResponseWriter, request *http.Request) {
	if request.Method != http.MethodGet && request.Method != http.MethodHead {
		writer.Header().Set("Allow", "GET, HEAD")
		http.Error(writer, "method not allowed", http.StatusMethodNotAllowed)
		return
	}
	requested := strings.TrimPrefix(path.Clean(request.URL.Path), "/")
	if requested == "." || requested == "" {
		requested = "index.html"
	}
	data, err := fs.ReadFile(a.options.Static, requested)
	if err != nil && !strings.HasPrefix(requested, "api/") {
		requested = "index.html"
		data, err = fs.ReadFile(a.options.Static, requested)
	}
	if err != nil {
		http.NotFound(writer, request)
		return
	}
	if contentType := mime.TypeByExtension(path.Ext(requested)); contentType != "" {
		writer.Header().Set("Content-Type", contentType)
	}
	writer.WriteHeader(http.StatusOK)
	if request.Method == http.MethodGet {
		_, _ = writer.Write(data)
	}
}

func decodeJSON(writer http.ResponseWriter, request *http.Request, target any) error {
	request.Body = http.MaxBytesReader(writer, request.Body, maxRequestBytes)
	decoder := json.NewDecoder(request.Body)
	decoder.DisallowUnknownFields()
	if err := decoder.Decode(target); err != nil {
		writeJSON(writer, http.StatusBadRequest, map[string]string{"error": "invalid request"})
		return err
	}
	if err := decoder.Decode(&struct{}{}); !errors.Is(err, io.EOF) {
		writeJSON(writer, http.StatusBadRequest, map[string]string{"error": "invalid request"})
		return errors.New("request contains trailing data")
	}
	return nil
}

func writeJSON(writer http.ResponseWriter, status int, value any) {
	writer.Header().Set("Content-Type", "application/json")
	writer.WriteHeader(status)
	_ = json.NewEncoder(writer).Encode(value)
}

// This is compatibility checking of trusted local assets, not a signature check.
func validateBundle(static fs.FS) error {
	const message = "incompatible browser bundle: rebuild core and browser from the same source"
	file, err := static.Open("forgeops-bundle.json")
	if err != nil {
		return errors.New(message)
	}
	defer file.Close()
	data, err := io.ReadAll(io.LimitReader(file, maxRequestBytes+1))
	if err != nil || len(data) > int(maxRequestBytes) {
		return errors.New(message)
	}
	decoder := json.NewDecoder(bytes.NewReader(data))
	decoder.DisallowUnknownFields()
	var identity console.BundleIdentity
	if decoder.Decode(&identity) != nil || identity != console.Bundle() {
		return errors.New(message)
	}
	if err := decoder.Decode(&struct{}{}); !errors.Is(err, io.EOF) {
		return errors.New(message)
	}
	return nil
}

func writeBrokerError(writer http.ResponseWriter, err error) {
	status, code := http.StatusInternalServerError, "internal_error"
	switch {
	case errors.Is(err, broker.ErrDenied):
		status, code = http.StatusForbidden, "capability_denied"
	case errors.Is(err, context.Canceled):
		status, code = http.StatusConflict, "cancelled"
	case errors.Is(err, context.DeadlineExceeded):
		status, code = http.StatusGatewayTimeout, "timeout"
	}
	writeJSON(writer, status, map[string]string{"error": code})
}
