package diagnostics

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"net/http/httptest"
	"strings"
	"sync"
	"testing"
	"time"
	"unicode/utf8"

	"github.com/wmstipes/The-Foundry-Initiative/apps/forgeops-console/internal/cluster"
	"github.com/wmstipes/The-Foundry-Initiative/apps/forgeops-console/internal/resources"
	"github.com/wmstipes/The-Foundry-Initiative/apps/forgeops-console/internal/session"
	corev1 "k8s.io/api/core/v1"
	apierrors "k8s.io/apimachinery/pkg/api/errors"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/apimachinery/pkg/runtime/schema"
	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/kubernetes/fake"
	"k8s.io/client-go/rest"
	clienttesting "k8s.io/client-go/testing"
	clientcmdapi "k8s.io/client-go/tools/clientcmd/api"
)

func fixture(t *testing.T, reader LogReader) (*Service, *session.State, *fake.Clientset, *resources.Service) {
	t.Helper()
	state, err := session.New([]string{"dev", "hostile'; $(touch nope)"})
	if err != nil {
		t.Fatal(err)
	}
	scope, err := state.SelectContext("dev")
	if err != nil {
		t.Fatal(err)
	}
	if err = state.AllowNamespaces(scope.Generation, []string{"team"}); err != nil {
		t.Fatal(err)
	}
	if _, err = state.SelectNamespace("team"); err != nil {
		t.Fatal(err)
	}
	client := fake.NewSimpleClientset(&corev1.Pod{ObjectMeta: metav1.ObjectMeta{Name: "api", Namespace: "team", UID: "pod-uid", Annotations: map[string]string{"token": "credential-marker"}}, Spec: corev1.PodSpec{Containers: []corev1.Container{{Name: "api"}}, InitContainers: []corev1.Container{{Name: "init"}}}})
	factory := cluster.ClientFactoryFunc(func(context.Context, *clientcmdapi.Config, string) (kubernetes.Interface, error) { return client, nil })
	raw := &clientcmdapi.Config{}
	records, err := resources.New(raw, state, factory)
	if err != nil {
		t.Fatal(err)
	}
	if reader == nil {
		reader = func(context.Context, kubernetes.Interface, string, string, *corev1.PodLogOptions) (io.ReadCloser, error) {
			return io.NopCloser(strings.NewReader("hello\n")), nil
		}
	}
	service, err := New(raw, state, factory, reader, records.RecordDiagnostic)
	if err != nil {
		t.Fatal(err)
	}
	return service, state, client, records
}
func logsQuery() Query { return Query{Generation: 2, Operation: "logs", Pod: "api", Container: "api"} }
func requireCode(t *testing.T, err error, code string) {
	t.Helper()
	var api *resources.APIError
	if !errors.As(err, &api) || api.Code != code {
		t.Fatalf("want %s, got %v", code, err)
	}
}

func TestLogOptionsAndMetadataOnlyActivity(t *testing.T) {
	service, _, client, records := fixture(t, func(_ context.Context, _ kubernetes.Interface, ns, pod string, o *corev1.PodLogOptions) (io.ReadCloser, error) {
		if ns != "team" || pod != "api" || o.Container != "api" || !o.Previous || o.Follow || *o.TailLines != MaxLines || *o.LimitBytes != MaxBytes {
			t.Fatalf("unsafe options: %#v", o)
		}
		return io.NopCloser(strings.NewReader("sensitive-application-text\n")), nil
	})
	q := logsQuery()
	q.Previous = true
	result, err := service.Execute(context.Background(), q)
	if err != nil {
		t.Fatal(err)
	}
	if !strings.Contains(result.Text, "sensitive-application-text") || !strings.Contains(result.Warning, "not guaranteed redacted") {
		t.Fatal("disclosure warning missing")
	}
	encoded, _ := json.Marshal(records.Activity())
	if strings.Contains(string(encoded), "sensitive") || strings.Contains(string(encoded), "credential-marker") {
		t.Fatal("content leaked to activity")
	}
	for _, action := range client.Actions() {
		if action.GetVerb() != "get" || action.GetResource().Resource != "pods" {
			t.Fatalf("unexpected action %v", action)
		}
	}
}

func TestInvalidQueriesNeverConstructClient(t *testing.T) {
	service, _, client, _ := fixture(t, nil)
	for _, q := range []Query{{Operation: "exec", Pod: "api"}, {Operation: "logs", Pod: "../api", Container: "api"}, {Operation: "logs", Pod: "api", Container: ""}, {Operation: "events", Pod: "api", Previous: true}, {Operation: "events", Pod: "api", Container: "api"}, {Operation: "logs", Pod: "api", Container: "api", Target: "logs"}, {Operation: "preview", Pod: "api", Target: "delete"}} {
		_, err := service.Execute(context.Background(), q)
		requireCode(t, err, "invalid_request")
	}
	if len(client.Actions()) != 0 {
		t.Fatal("invalid request reached client")
	}
}

func TestStaleScopeAndMissingNamespace(t *testing.T) {
	service, state, client, _ := fixture(t, nil)
	if _, err := state.SelectContext("dev"); err != nil {
		t.Fatal(err)
	}
	_, err := service.Execute(context.Background(), logsQuery())
	requireCode(t, err, "stale_scope")
	q := logsQuery()
	q.Generation = 3
	_, err = service.Execute(context.Background(), q)
	requireCode(t, err, "namespace_required")
	if len(client.Actions()) != 0 {
		t.Fatal("invalid scope reached client")
	}
}

func TestContainerMustExistOnCurrentPod(t *testing.T) {
	service, _, _, _ := fixture(t, func(context.Context, kubernetes.Interface, string, string, *corev1.PodLogOptions) (io.ReadCloser, error) {
		t.Fatal("unexpected log read")
		return nil, nil
	})
	q := logsQuery()
	q.Container = "absent"
	_, err := service.Execute(context.Background(), q)
	requireCode(t, err, "invalid_container")
}

func TestLogByteLineAndControlBounds(t *testing.T) {
	for _, input := range []string{strings.Repeat("x", MaxBytes+20), strings.Repeat("x\n", MaxLines+20)} {
		service, _, _, _ := fixture(t, func(context.Context, kubernetes.Interface, string, string, *corev1.PodLogOptions) (io.ReadCloser, error) {
			return io.NopCloser(strings.NewReader(input)), nil
		})
		result, err := service.Execute(context.Background(), logsQuery())
		if err != nil {
			t.Fatal(err)
		}
		if !result.Truncated || len(result.Text) > MaxBytes || strings.Count(result.Text, "\n") > MaxLines {
			t.Fatal("bounds not enforced")
		}
	}
	value := safeText("<script>alert(1)</script>\x1b[31m\r\x00\u202e\xff\n\t", 200)
	if strings.ContainsAny(value, "\x1b\r\x00\u202e") || !utf8.ValidString(value) || !strings.Contains(value, "<script>") {
		t.Fatalf("unexpected sanitization %q", value)
	}
	if len(safeText(strings.Repeat("\x00", 100), 20)) > 20 {
		t.Fatal("replacement expansion escaped bound")
	}
}

func TestEventProjectionFilteringPaginationAndTextBounds(t *testing.T) {
	service, _, client, _ := fixture(t, nil)
	client.PrependReactor("list", "events", func(action clienttesting.Action) (bool, runtime.Object, error) {
		selector := action.(clienttesting.ListAction).GetListRestrictions().Fields.String()
		if !strings.Contains(selector, "involvedObject.uid=pod-uid") || action.GetNamespace() != "team" {
			t.Fatalf("unsafe selector %s", selector)
		}
		events := []corev1.Event{}
		for i := 0; i < MaxEvents+1; i++ {
			events = append(events, corev1.Event{ObjectMeta: metav1.ObjectMeta{Name: fmt.Sprintf("event-%03d", i), Namespace: "team", Annotations: map[string]string{"token": "credential-marker"}}, InvolvedObject: corev1.ObjectReference{UID: "pod-uid", Name: "api", Kind: "Pod", Namespace: "team"}, Message: strings.Repeat("x", 2000) + "\x1b", Reason: "Started", Type: "Normal", Count: 1})
		}
		events[0].InvolvedObject.UID = "old-pod"
		return true, &corev1.EventList{ListMeta: metav1.ListMeta{Continue: "next"}, Items: events}, nil
	})
	result, err := service.Execute(context.Background(), Query{Generation: 2, Operation: "events", Pod: "api"})
	if err != nil {
		t.Fatal(err)
	}
	if !result.Truncated || len(result.Events) != MaxEvents-1 || len(result.Events[0].Message) != 1024 {
		t.Fatal("event bound/filter failed")
	}
	encoded, _ := json.Marshal(result)
	if strings.Contains(string(encoded), "credential-marker") {
		t.Fatal("raw metadata leaked")
	}
}

type blockingStream struct {
	once   sync.Once
	closed chan struct{}
}

func (s *blockingStream) Read([]byte) (int, error) { <-s.closed; return 0, io.ErrClosedPipe }
func (s *blockingStream) Close() error             { s.once.Do(func() { close(s.closed) }); return nil }

func TestCancellationScopeChangeAndDeadlineCloseStream(t *testing.T) {
	for _, mode := range []string{"cancel", "scope", "deadline"} {
		t.Run(mode, func(t *testing.T) {
			stream := &blockingStream{closed: make(chan struct{})}
			started := make(chan struct{})
			service, state, _, _ := fixture(t, func(context.Context, kubernetes.Interface, string, string, *corev1.PodLogOptions) (io.ReadCloser, error) {
				close(started)
				return stream, nil
			})
			ctx, cancel := context.WithCancel(context.Background())
			defer cancel()
			if mode == "deadline" {
				var stop context.CancelFunc
				ctx, stop = context.WithTimeout(ctx, 50*time.Millisecond)
				defer stop()
			}
			done := make(chan error, 1)
			go func() {
				result, err := service.Execute(ctx, logsQuery())
				if result.Text != "" {
					done <- errors.New("partial text escaped")
					return
				}
				done <- err
			}()
			<-started
			want := "cancelled"
			if mode == "scope" {
				_, _ = state.SelectContext("dev")
				want = "stale_scope"
			} else if mode == "deadline" {
				want = "timeout"
			} else {
				cancel()
			}
			select {
			case err := <-done:
				requireCode(t, err, want)
			case <-time.After(time.Second):
				t.Fatal("request did not stop")
			}
			select {
			case <-stream.closed:
			default:
				t.Fatal("stream not closed")
			}
		})
	}
}

func TestConcurrencyCapAndSlotRecovery(t *testing.T) {
	started := make(chan struct{}, MaxConcurrent)
	service, _, _, _ := fixture(t, func(context.Context, kubernetes.Interface, string, string, *corev1.PodLogOptions) (io.ReadCloser, error) {
		started <- struct{}{}
		return &blockingStream{closed: make(chan struct{})}, nil
	})
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	var wg sync.WaitGroup
	for i := 0; i < MaxConcurrent; i++ {
		wg.Add(1)
		go func() { defer wg.Done(); _, _ = service.Execute(ctx, logsQuery()) }()
	}
	for i := 0; i < MaxConcurrent; i++ {
		<-started
	}
	_, err := service.Execute(context.Background(), logsQuery())
	requireCode(t, err, "busy")
	cancel()
	wg.Wait()
	if len(service.slots) != 0 {
		t.Fatal("slot leak")
	}
}

func TestUpstreamErrorsAreSanitizedAndPartialLogsDiscarded(t *testing.T) {
	for _, tc := range []struct {
		err  error
		code string
	}{
		{apierrors.NewForbidden(schema.GroupResource{Resource: "pods"}, "api", errors.New("credential-marker")), "forbidden"},
		{apierrors.NewUnauthorized("credential-marker"), "unauthenticated"},
		{apierrors.NewNotFound(schema.GroupResource{Resource: "pods"}, "api"), "not_found"},
		{errors.New("credential-marker disconnected"), "unavailable"},
		{context.DeadlineExceeded, "timeout"},
	} {
		service, _, _, records := fixture(t, func(context.Context, kubernetes.Interface, string, string, *corev1.PodLogOptions) (io.ReadCloser, error) {
			return nil, tc.err
		})
		_, err := service.Execute(context.Background(), logsQuery())
		requireCode(t, err, tc.code)
		encoded, _ := json.Marshal(records.Activity())
		if strings.Contains(string(encoded), "credential-marker") {
			t.Fatal("upstream details leaked")
		}
	}
	service, _, _, _ := fixture(t, func(context.Context, kubernetes.Interface, string, string, *corev1.PodLogOptions) (io.ReadCloser, error) {
		return io.NopCloser(&brokenReader{}), nil
	})
	result, err := service.Execute(context.Background(), logsQuery())
	requireCode(t, err, "unavailable")
	if result.Text != "" {
		t.Fatal("partial result escaped")
	}
}

type brokenReader struct{}

func (*brokenReader) Read(p []byte) (int, error) {
	return copy(p, "private partial"), io.ErrUnexpectedEOF
}

func TestPreviewIsOfflineQuotedAndHonest(t *testing.T) {
	service, state, client, _ := fixture(t, nil)
	scope, _ := state.SelectContext("hostile'; $(touch nope)")
	_ = state.AllowNamespaces(scope.Generation, []string{"team"})
	scope, _ = state.SelectNamespace("team")
	q := logsQuery()
	q.Generation = scope.Generation
	q.Operation = "preview"
	q.Target = "logs"
	result, err := service.Execute(context.Background(), q)
	if err != nil {
		t.Fatal(err)
	}
	if len(client.Actions()) != 0 || !strings.Contains(result.Preview.PowerShell, "hostile''; $(touch nope)") || !strings.Contains(result.Preview.POSIX, `hostile'"'"'; $(touch nope)`) {
		t.Fatalf("quoting failed %#v", result.Preview)
	}
	if !strings.Contains(result.Preview.Note, "No exact CLI equivalent") || !strings.Contains(result.Preview.PowerShell, "<explicit-kubeconfig>") {
		t.Fatal("preview overstated equivalence")
	}
}

func TestProductionLogReaderUsesOnlyFixedTypedGETs(t *testing.T) {
	var mu sync.Mutex
	paths := []string{}
	upstream := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		mu.Lock()
		paths = append(paths, r.URL.Path)
		mu.Unlock()
		if r.Method != "GET" {
			t.Error("non-read request")
		}
		switch r.URL.Path {
		case "/api/v1/namespaces/team/pods/api":
			w.Header().Set("Content-Type", "application/json")
			_, _ = io.WriteString(w, `{"apiVersion":"v1","kind":"Pod","metadata":{"name":"api","namespace":"team","uid":"pod-uid"},"spec":{"containers":[{"name":"api"}]}}`)
		case "/api/v1/namespaces/team/pods/api/log":
			q := r.URL.Query()
			if q.Get("container") != "api" || q.Get("tailLines") != "500" || q.Get("limitBytes") != "65536" || q.Get("follow") == "true" {
				t.Errorf("unsafe query %v", q)
			}
			_, _ = io.WriteString(w, "typed client log\n")
		default:
			t.Error("unexpected API path")
			http.NotFound(w, r)
		}
	}))
	defer upstream.Close()
	client, err := kubernetes.NewForConfig(&rest.Config{Host: upstream.URL})
	if err != nil {
		t.Fatal(err)
	}
	_, state, _, records := fixture(t, nil)
	service, err := New(&clientcmdapi.Config{}, state, cluster.ClientFactoryFunc(func(ctx context.Context, _ *clientcmdapi.Config, _ string) (kubernetes.Interface, error) {
		deadline, ok := ctx.Deadline()
		if !ok || time.Until(deadline) > Timeout {
			t.Error("missing core timeout")
		}
		return client, nil
	}), nil, records.RecordDiagnostic)
	if err != nil {
		t.Fatal(err)
	}
	result, err := service.Execute(context.Background(), logsQuery())
	if err != nil || result.Text != "typed client log\n" {
		t.Fatalf("typed stream %v %#v", err, result)
	}
	mu.Lock()
	defer mu.Unlock()
	if len(paths) != 2 {
		t.Fatalf("unexpected requests %v", paths)
	}
}

func TestEncodedResponseLimitRejectsJSONExpansion(t *testing.T) {
	service, _, _, _ := fixture(t, func(context.Context, kubernetes.Interface, string, string, *corev1.PodLogOptions) (io.ReadCloser, error) {
		return io.NopCloser(strings.NewReader(strings.Repeat("<", MaxBytes))), nil
	})
	result, err := service.Execute(context.Background(), logsQuery())
	requireCode(t, err, "too_large")
	if result.Text != "" {
		t.Fatal("oversized payload escaped")
	}
}
