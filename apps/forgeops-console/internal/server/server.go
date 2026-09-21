package server

import (
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

	"github.com/wmstipes/The-Foundry-Initiative/apps/forgeops-console/internal/broker"
	"github.com/wmstipes/The-Foundry-Initiative/apps/forgeops-console/internal/config"
	"github.com/wmstipes/The-Foundry-Initiative/apps/forgeops-console/internal/plugins"
	"github.com/wmstipes/The-Foundry-Initiative/apps/forgeops-console/internal/session"
)

const maxRequestBytes int64 = 4 << 10

type Options struct {
	AllowedHost string
	Contexts    []config.ContextSummary
	State       *session.State
	Registry    *plugins.Registry
	Broker      *broker.Broker
	Static      fs.FS
	Nonce       string
}

type api struct {
	options Options
}

type bootstrapResponse struct {
	Mode            string                  `json:"mode"`
	SessionNonce    string                  `json:"sessionNonce"`
	SelectedContext string                  `json:"selectedContext"`
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
	if options.State == nil || options.Registry == nil || options.Broker == nil || options.Static == nil || options.Nonce == "" {
		return nil, errors.New("server options are incomplete")
	}
	application := &api{options: options}
	mux := http.NewServeMux()
	mux.HandleFunc("GET /healthz", application.health)
	mux.HandleFunc("GET /api/v1/bootstrap", application.bootstrap)
	mux.HandleFunc("POST /api/v1/context", application.selectContext)
	mux.HandleFunc("POST /api/v1/plugins/forge.example/status", application.exampleStatus)
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
	writeJSON(writer, http.StatusOK, map[string]string{"status": "ok", "mode": "offline-c2"})
}

func (a *api) bootstrap(writer http.ResponseWriter, _ *http.Request) {
	writeJSON(writer, http.StatusOK, bootstrapResponse{
		Mode:            "offline-c2",
		SessionNonce:    a.options.Nonce,
		SelectedContext: a.options.State.Selected(),
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
	if err := a.options.State.Select(input.Context); err != nil {
		writeJSON(writer, http.StatusBadRequest, map[string]string{"error": "unknown context"})
		return
	}
	writeJSON(writer, http.StatusOK, map[string]string{"selectedContext": a.options.State.Selected()})
}

func (a *api) exampleStatus(writer http.ResponseWriter, request *http.Request) {
	if !a.validNonce(request) {
		http.Error(writer, "session denied", http.StatusForbidden)
		return
	}
	response, err := a.options.Broker.Invoke(request.Context(), plugins.ExamplePluginID, plugins.ExampleStatusCapability, broker.Request{})
	if err != nil {
		writeJSON(writer, http.StatusForbidden, map[string]string{"error": "capability denied"})
		return
	}
	writeJSON(writer, http.StatusOK, response)
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
