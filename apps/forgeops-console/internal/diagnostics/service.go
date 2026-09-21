// Package diagnostics owns bounded Pod diagnostics. It never executes commands.
package diagnostics

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"sort"
	"strings"
	"time"
	"unicode"

	corev1 "k8s.io/api/core/v1"
	apierrors "k8s.io/apimachinery/pkg/api/errors"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/fields"
	"k8s.io/apimachinery/pkg/util/validation"
	"k8s.io/client-go/kubernetes"
	clientcmdapi "k8s.io/client-go/tools/clientcmd/api"

	"github.com/wmstipes/The-Foundry-Initiative/apps/forgeops-console/internal/cluster"
	"github.com/wmstipes/The-Foundry-Initiative/apps/forgeops-console/internal/resources"
	"github.com/wmstipes/The-Foundry-Initiative/apps/forgeops-console/internal/session"
)

const (
	Timeout          = 5 * time.Second
	MaxBytes         = 64 << 10
	MaxLines         = 500
	MaxEvents        = 100
	MaxConcurrent    = 2
	MaxResponseBytes = 256 << 10
	Warning          = "Logs and Events may contain credentials or personal data. Text is not guaranteed redacted. Review before sharing; no export or execution is provided."
)

type Query struct {
	Generation uint64 `json:"generation"`
	Operation  string `json:"operation"`
	Pod        string `json:"pod"`
	Container  string `json:"container,omitempty"`
	Previous   bool   `json:"previous,omitempty"`
	Target     string `json:"target,omitempty"`
}
type Event struct {
	Name    string `json:"name"`
	Type    string `json:"type"`
	Reason  string `json:"reason"`
	Message string `json:"message"`
	Count   int32  `json:"count"`
}
type Preview struct {
	PowerShell string `json:"powershell"`
	POSIX      string `json:"posix"`
	Note       string `json:"note"`
}
type Result struct {
	Scope     session.Scope `json:"scope"`
	Operation string        `json:"operation"`
	Text      string        `json:"text"`
	Events    []Event       `json:"events"`
	Truncated bool          `json:"truncated"`
	Warning   string        `json:"warning"`
	Preview   *Preview      `json:"preview,omitempty"`
}

// LogReader is core-owned and injectable for offline tests/demo only.
type LogReader func(context.Context, kubernetes.Interface, string, string, *corev1.PodLogOptions) (io.ReadCloser, error)
type Service struct {
	raw     *clientcmdapi.Config
	state   *session.State
	factory cluster.ClientFactory
	logs    LogReader
	slots   chan struct{}
	record  func(resources.Activity)
}

func New(raw *clientcmdapi.Config, state *session.State, factory cluster.ClientFactory, logs LogReader, record func(resources.Activity)) (*Service, error) {
	if raw == nil || state == nil || factory == nil || record == nil {
		return nil, errors.New("diagnostic dependencies required")
	}
	if logs == nil {
		logs = func(ctx context.Context, client kubernetes.Interface, ns, pod string, options *corev1.PodLogOptions) (io.ReadCloser, error) {
			return client.CoreV1().Pods(ns).GetLogs(pod, options).Stream(ctx)
		}
	}
	return &Service{raw: raw.DeepCopy(), state: state, factory: factory, logs: logs, slots: make(chan struct{}, MaxConcurrent), record: record}, nil
}

func valid(q Query) bool {
	target := q.Operation
	if target == "preview" {
		target = q.Target
	} else if q.Target != "" {
		return false
	}
	if len(validation.IsDNS1123Subdomain(q.Pod)) != 0 {
		return false
	}
	switch target {
	case "logs":
		return len(validation.IsDNS1123Label(q.Container)) == 0
	case "events":
		return q.Container == "" && !q.Previous
	default:
		return false
	}
}

func (s *Service) Execute(parent context.Context, q Query) (result Result, err error) {
	if !valid(q) {
		return Result{}, &resources.APIError{Code: "invalid_request", Status: 400}
	}
	request, cancelScope, scope, err := s.state.RequestContext(parent, q.Generation)
	if err != nil {
		return Result{}, &resources.APIError{Code: "stale_scope", Status: 409}
	}
	defer cancelScope()
	capability := map[string]string{"logs": "pods.logs.read", "events": "events.read", "preview": "command.preview"}[q.Operation]
	defer func() {
		outcome := "ok"
		if err != nil {
			result = Result{}
			mapped := mapError(err)
			err = mapped
			outcome = mapped.Code
		}
		s.record(resources.Activity{Capability: capability, Context: scope.Context, Namespace: scope.Namespace, Generation: scope.Generation, Outcome: outcome, ItemCount: len(result.Events), Truncated: result.Truncated})
	}()
	if scope.Namespace == "" {
		return Result{}, &resources.APIError{Code: "namespace_required", Status: 400}
	}
	ctx, cancel := context.WithTimeout(request, Timeout)
	defer cancel()
	select {
	case s.slots <- struct{}{}:
		defer func() { <-s.slots }()
	default:
		return Result{}, &resources.APIError{Code: "busy", Status: 429}
	}
	result = Result{Scope: scope, Operation: q.Operation, Events: []Event{}, Warning: Warning}
	if q.Operation == "preview" {
		result.Preview, err = preview(scope, q)
	} else {
		var client kubernetes.Interface
		client, err = s.factory.ClientFor(ctx, s.raw, scope.Context)
		if err == nil {
			var pod *corev1.Pod
			pod, err = client.CoreV1().Pods(scope.Namespace).Get(ctx, q.Pod, metav1.GetOptions{})
			if err == nil {
				if pod.Name != q.Pod || pod.Namespace != scope.Namespace || pod.UID == "" {
					return Result{}, errors.New("invalid pod response")
				}
				if q.Operation == "logs" {
					result.Text, result.Truncated, err = s.readLogs(ctx, client, scope, pod, q)
				} else {
					result.Events, result.Truncated, err = readEvents(ctx, client, scope, pod)
				}
			}
		}
	}
	if s.state.Current().Generation != scope.Generation {
		return Result{}, session.ErrStaleScope
	}
	if ctx.Err() != nil {
		return Result{}, ctx.Err()
	}
	if err != nil {
		return Result{}, err
	}
	encoded, encodeErr := json.Marshal(result)
	if encodeErr != nil || len(encoded) > MaxResponseBytes {
		return Result{}, &resources.APIError{Code: "too_large", Status: 413}
	}
	return result, nil
}

func (s *Service) readLogs(ctx context.Context, client kubernetes.Interface, scope session.Scope, pod *corev1.Pod, q Query) (string, bool, error) {
	found := false
	for _, c := range pod.Spec.Containers {
		if c.Name == q.Container {
			found = true
		}
	}
	for _, c := range pod.Spec.InitContainers {
		if c.Name == q.Container {
			found = true
		}
	}
	if !found {
		return "", false, &resources.APIError{Code: "invalid_container", Status: 400}
	}
	lines, limit := int64(MaxLines), int64(MaxBytes)
	stream, err := s.logs(ctx, client, scope.Namespace, q.Pod, &corev1.PodLogOptions{Container: q.Container, Previous: q.Previous, Follow: false, TailLines: &lines, LimitBytes: &limit})
	if err != nil {
		return "", false, err
	}
	defer stream.Close()
	stop := context.AfterFunc(ctx, func() { _ = stream.Close() })
	defer stop()
	data, err := io.ReadAll(io.LimitReader(stream, MaxBytes+1))
	if ctx.Err() != nil {
		return "", false, ctx.Err()
	}
	if err != nil {
		return "", false, err
	}
	// Equality is conservatively marked: the server may have applied LimitBytes.
	truncated := len(data) >= MaxBytes
	if len(data) > MaxBytes {
		data = data[:MaxBytes]
	}
	text := string(data)
	count := 0
	for i, c := range text {
		if c == '\n' {
			count++
			if count == MaxLines {
				truncated = true
				text = text[:i+1]
				break
			}
		}
	}
	clean, clipped := safeTextBounded(text, MaxBytes)
	return clean, truncated || clipped, nil
}

func readEvents(ctx context.Context, client kubernetes.Interface, scope session.Scope, pod *corev1.Pod) ([]Event, bool, error) {
	selector := fields.Set{"involvedObject.uid": string(pod.UID), "involvedObject.name": pod.Name, "involvedObject.kind": "Pod", "involvedObject.namespace": scope.Namespace}.AsSelector().String()
	list, err := client.CoreV1().Events(scope.Namespace).List(ctx, metav1.ListOptions{FieldSelector: selector, Limit: MaxEvents + 1})
	if err != nil {
		return nil, false, err
	}
	truncated := list.Continue != "" || len(list.Items) > MaxEvents
	items := list.Items
	if len(items) > MaxEvents {
		items = items[:MaxEvents]
	}
	result := []Event{}
	for _, e := range items {
		if e.Namespace != scope.Namespace || e.InvolvedObject.UID != pod.UID || e.InvolvedObject.Kind != "Pod" || e.InvolvedObject.Name != pod.Name || e.InvolvedObject.Namespace != scope.Namespace {
			continue
		}
		if len(e.Message) > 1024 || len(e.Reason) > 128 || len(e.Type) > 32 || len(e.Name) > 253 {
			truncated = true
		}
		clean := func(value string, limit int) string {
			text, clipped := safeTextBounded(value, limit)
			truncated = truncated || clipped
			return text
		}
		result = append(result, Event{Name: clean(e.Name, 253), Type: clean(e.Type, 32), Reason: clean(e.Reason, 128), Message: clean(e.Message, 1024), Count: e.Count})
	}
	sort.Slice(result, func(i, j int) bool { return result[i].Name < result[j].Name })
	return result, truncated, nil
}

// Bound input and output; replace terminal/bidi/format controls and invalid UTF-8.
func safeText(value string, limit int) string {
	text, _ := safeTextBounded(value, limit)
	return text
}

func safeTextBounded(value string, limit int) (string, bool) {
	clipped := len(value) > limit
	if len(value) > limit {
		value = value[:limit]
	}
	var out strings.Builder
	for _, r := range value {
		if (unicode.IsControl(r) && r != '\n' && r != '\t') || unicode.Is(unicode.Cf, r) {
			r = '�'
		}
		piece := string(r)
		if out.Len()+len(piece) > limit {
			clipped = true
			break
		}
		out.WriteString(piece)
	}
	return out.String(), clipped
}

func preview(scope session.Scope, q Query) (*Preview, error) {
	if len(scope.Context) > 253 || safeText(scope.Context, 253) != scope.Context || strings.ContainsAny(scope.Context, "\n\t") {
		return nil, &resources.APIError{Code: "invalid_request", Status: 400}
	}
	args := []string{"--kubeconfig=<explicit-kubeconfig>", "--context=" + scope.Context, "--namespace=" + scope.Namespace}
	if q.Target == "logs" {
		args = append(args, "logs", q.Pod, "--container="+q.Container, "--tail=500", "--limit-bytes=65536", "--follow=false", fmt.Sprintf("--previous=%t", q.Previous))
	} else {
		args = append(args, "get", "events", "--field-selector=involvedObject.kind=Pod,involvedObject.name="+q.Pod)
	}
	args = append(args, "--request-timeout=5s")
	ps, posix := []string{"kubectl"}, []string{"kubectl"}
	for _, arg := range args {
		ps = append(ps, "'"+strings.ReplaceAll(arg, "'", "''")+"'")
		posix = append(posix, "'"+strings.ReplaceAll(arg, "'", "'\"'\"'")+"'")
	}
	return &Preview{PowerShell: strings.Join(ps, " "), POSIX: strings.Join(posix, " "), Note: "Explanation only; not executed. Replace the kubeconfig placeholder manually. No exact CLI equivalent: Console validates the Pod/container, binds generation, projects/sanitizes text and enforces extra bounds. Event preview is name-scoped; Console additionally matches the current Pod UID. Preview does not contact the cluster or prove object existence/permission."}, nil
}

func mapError(err error) *resources.APIError {
	var known *resources.APIError
	if errors.As(err, &known) {
		return known
	}
	switch {
	case errors.Is(err, session.ErrStaleScope):
		return &resources.APIError{Code: "stale_scope", Status: 409}
	case errors.Is(err, context.Canceled):
		return &resources.APIError{Code: "cancelled", Status: 409}
	case errors.Is(err, context.DeadlineExceeded), apierrors.IsTimeout(err), apierrors.IsServerTimeout(err):
		return &resources.APIError{Code: "timeout", Status: 504}
	case apierrors.IsForbidden(err):
		return &resources.APIError{Code: "forbidden", Status: 403}
	case apierrors.IsUnauthorized(err):
		return &resources.APIError{Code: "unauthenticated", Status: 401}
	case apierrors.IsNotFound(err):
		return &resources.APIError{Code: "not_found", Status: 404}
	default:
		return &resources.APIError{Code: "unavailable", Status: 503}
	}
}
