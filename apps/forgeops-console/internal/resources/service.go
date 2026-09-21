package resources

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"sort"
	"strconv"
	"strings"
	"sync"
	"time"

	appsv1 "k8s.io/api/apps/v1"
	corev1 "k8s.io/api/core/v1"
	discoveryv1 "k8s.io/api/discovery/v1"
	apierrors "k8s.io/apimachinery/pkg/api/errors"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/labels"
	"k8s.io/apimachinery/pkg/runtime/schema"
	"k8s.io/apimachinery/pkg/util/validation"
	"k8s.io/client-go/kubernetes"
	clientcmdapi "k8s.io/client-go/tools/clientcmd/api"

	"github.com/wmstipes/The-Foundry-Initiative/apps/forgeops-console/internal/cluster"
	"github.com/wmstipes/The-Foundry-Initiative/apps/forgeops-console/internal/session"
)

const (
	RequestTimeout   = 5 * time.Second
	MaxConcurrent    = 4
	MaxObjects       = 200
	MaxResponseBytes = 1 << 20
	MaxActivity      = 100
)

var allowedKinds = map[string]bool{
	"namespaces": true, "nodes": true, "deployments": true,
	"replicasets": true, "pods": true, "services": true, "endpointslices": true,
}

type Query struct {
	Generation uint64 `json:"generation"`
	Operation  string `json:"operation"`
	Resource   string `json:"resource"`
	Name       string `json:"name,omitempty"`
}

type Field struct {
	Label string `json:"label"`
	Value string `json:"value"`
}

type Reference struct {
	Kind      string `json:"kind"`
	Name      string `json:"name"`
	Namespace string `json:"namespace,omitempty"`
	Relation  string `json:"relation"`
}

type Record struct {
	Kind      string      `json:"kind"`
	Name      string      `json:"name"`
	Namespace string      `json:"namespace,omitempty"`
	Status    string      `json:"status"`
	Fields    []Field     `json:"fields"`
	Owners    []Reference `json:"owners"`
	Related   []Reference `json:"related"`
}

type Result struct {
	Resource  string        `json:"resource"`
	Operation string        `json:"operation"`
	Scope     session.Scope `json:"scope"`
	Items     []Record      `json:"items"`
	Truncated bool          `json:"truncated"`
}

type APIError struct {
	Code   string
	Status int
}

func (e *APIError) Error() string { return e.Code }

type Activity struct {
	Sequence   uint64 `json:"sequence"`
	Capability string `json:"capability"`
	Context    string `json:"context"`
	Namespace  string `json:"namespace,omitempty"`
	Generation uint64 `json:"generation"`
	Outcome    string `json:"outcome"`
	ItemCount  int    `json:"itemCount"`
	Truncated  bool   `json:"truncated"`
}

type Service struct {
	raw      *clientcmdapi.Config
	state    *session.State
	factory  cluster.ClientFactory
	requests chan struct{}
	mu       sync.Mutex
	sequence uint64
	activity []Activity
}

func New(raw *clientcmdapi.Config, state *session.State, factory cluster.ClientFactory) (*Service, error) {
	if raw == nil || state == nil || factory == nil {
		return nil, errors.New("resource service dependencies are required")
	}
	return &Service{raw: raw.DeepCopy(), state: state, factory: factory, requests: make(chan struct{}, MaxConcurrent)}, nil
}

func (s *Service) Execute(parent context.Context, query Query) (Result, error) {
	if !allowedKinds[query.Resource] || (query.Operation != "list" && query.Operation != "read") ||
		(query.Operation == "list" && query.Name != "") || (query.Operation == "read" && strings.TrimSpace(query.Name) == "") {
		return Result{}, &APIError{Code: "invalid_request", Status: 400}
	}
	if query.Operation == "read" && len(validation.IsDNS1123Subdomain(query.Name)) != 0 {
		return Result{}, &APIError{Code: "invalid_request", Status: 400}
	}
	requestContext, cancelScope, scope, err := s.state.RequestContext(parent, query.Generation)
	if err != nil {
		return Result{}, &APIError{Code: "stale_scope", Status: 409}
	}
	defer cancelScope()
	if query.Resource != "namespaces" && query.Resource != "nodes" && scope.Namespace == "" {
		return Result{}, &APIError{Code: "namespace_required", Status: 409}
	}
	ctx, cancel := context.WithTimeout(requestContext, RequestTimeout)
	defer cancel()
	select {
	case s.requests <- struct{}{}:
		defer func() { <-s.requests }()
	case <-ctx.Done():
		return Result{}, s.finishError(scope, query, ctx.Err())
	}
	client, err := s.factory.ClientFor(ctx, s.raw, scope.Context)
	if err != nil {
		return Result{}, s.finishError(scope, query, err)
	}
	items, truncated, err := s.project(ctx, client, scope, query)
	if err != nil {
		return Result{}, s.finishError(scope, query, err)
	}
	if query.Operation == "read" {
		exact := make([]Record, 0, 1)
		for _, item := range items {
			if item.Name == query.Name {
				exact = append(exact, item)
				break
			}
		}
		items = exact
		truncated = false
	}
	if current := s.state.Current(); current.Generation != scope.Generation {
		return Result{}, s.finishError(scope, query, session.ErrStaleScope)
	}
	if query.Operation == "read" && len(items) == 0 {
		return Result{}, s.finishError(scope, query, apierrors.NewNotFound(schema.GroupResource{Resource: query.Resource}, query.Name))
	}
	for index := range items {
		if items[index].Fields == nil {
			items[index].Fields = []Field{}
		}
		if items[index].Owners == nil {
			items[index].Owners = []Reference{}
		}
		if items[index].Related == nil {
			items[index].Related = []Reference{}
		}
	}
	result := Result{Resource: query.Resource, Operation: query.Operation, Scope: scope, Items: items, Truncated: truncated}
	encoded, err := json.Marshal(result)
	if err != nil || len(encoded) > MaxResponseBytes {
		return Result{}, s.finishError(scope, query, errors.New("response too large"))
	}
	s.record(Activity{Capability: "resources.read", Context: scope.Context, Namespace: scope.Namespace, Generation: scope.Generation, Outcome: "ok", ItemCount: len(items), Truncated: truncated})
	return result, nil
}

func (s *Service) finishError(scope session.Scope, query Query, err error) error {
	mapped := mapError(err)
	s.record(Activity{Capability: "resources.read", Context: scope.Context, Namespace: scope.Namespace, Generation: scope.Generation, Outcome: mapped.Code})
	return mapped
}

func mapError(err error) *APIError {
	switch {
	case errors.Is(err, session.ErrStaleScope), errors.Is(err, context.Canceled):
		return &APIError{Code: "stale_scope", Status: 409}
	case errors.Is(err, context.DeadlineExceeded), apierrors.IsTimeout(err), apierrors.IsServerTimeout(err):
		return &APIError{Code: "timeout", Status: 504}
	case apierrors.IsForbidden(err):
		return &APIError{Code: "forbidden", Status: 403}
	case apierrors.IsUnauthorized(err):
		return &APIError{Code: "unauthenticated", Status: 401}
	case apierrors.IsNotFound(err):
		return &APIError{Code: "not_found", Status: 404}
	case err != nil && err.Error() == "response too large":
		return &APIError{Code: "too_large", Status: 413}
	default:
		return &APIError{Code: "unavailable", Status: 503}
	}
}

func (s *Service) record(entry Activity) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.sequence++
	entry.Sequence = s.sequence
	s.activity = append(s.activity, entry)
	if len(s.activity) > MaxActivity {
		s.activity = append([]Activity(nil), s.activity[len(s.activity)-MaxActivity:]...)
	}
}

// RecordDiagnostic retains only fixed metadata, never logs, Events or previews.
func (s *Service) RecordDiagnostic(entry Activity) { s.record(entry) }

func (s *Service) Activity() []Activity {
	s.mu.Lock()
	defer s.mu.Unlock()
	return append([]Activity(nil), s.activity...)
}

func listOptions(query Query) metav1.ListOptions {
	options := metav1.ListOptions{Limit: MaxObjects + 1}
	if query.Operation == "read" {
		options.FieldSelector = "metadata.name=" + query.Name
		options.Limit = 2
	}
	return options
}

func trim(records []Record) ([]Record, bool, error) {
	sort.Slice(records, func(i, j int) bool { return records[i].Name < records[j].Name })
	if len(records) > MaxObjects {
		return records[:MaxObjects], true, nil
	}
	return records, false, nil
}

func owners(namespace string, references []metav1.OwnerReference) []Reference {
	result := make([]Reference, 0, len(references))
	for _, owner := range references {
		result = append(result, Reference{Kind: owner.Kind, Name: owner.Name, Namespace: namespace, Relation: "owned-by"})
	}
	return result
}

func (s *Service) project(ctx context.Context, client kubernetes.Interface, scope session.Scope, query Query) ([]Record, bool, error) {
	options := listOptions(query)
	switch query.Resource {
	case "namespaces":
		list, err := client.CoreV1().Namespaces().List(ctx, options)
		if err != nil {
			return nil, false, err
		}
		records := make([]Record, 0, len(list.Items))
		for _, item := range list.Items {
			records = append(records, Record{Kind: "Namespace", Name: item.Name, Status: string(item.Status.Phase), Fields: []Field{{Label: "Phase", Value: string(item.Status.Phase)}}})
		}
		records, truncated, _ := trim(records)
		names := make([]string, 0, len(records))
		for _, item := range records {
			names = append(names, item.Name)
		}
		if query.Operation == "list" {
			if err := s.state.AllowNamespaces(scope.Generation, names); err != nil {
				return nil, false, err
			}
		}
		return records, truncated, nil
	case "nodes":
		list, err := client.CoreV1().Nodes().List(ctx, options)
		if err != nil {
			return nil, false, err
		}
		records := make([]Record, 0, len(list.Items))
		for _, item := range list.Items {
			records = append(records, projectNode(item))
		}
		return trim(records)
	case "pods":
		list, err := client.CoreV1().Pods(scope.Namespace).List(ctx, options)
		if err != nil {
			return nil, false, err
		}
		records := make([]Record, 0, len(list.Items))
		for _, item := range list.Items {
			records = append(records, projectPod(item))
		}
		return trim(records)
	case "deployments":
		list, err := client.AppsV1().Deployments(scope.Namespace).List(ctx, options)
		if err != nil {
			return nil, false, err
		}
		pods, err := client.CoreV1().Pods(scope.Namespace).List(ctx, metav1.ListOptions{Limit: MaxObjects + 1})
		if err != nil {
			return nil, false, err
		}
		records := make([]Record, 0, len(list.Items))
		for _, item := range list.Items {
			records = append(records, projectDeployment(item, pods.Items))
		}
		return trim(records)
	case "replicasets":
		list, err := client.AppsV1().ReplicaSets(scope.Namespace).List(ctx, options)
		if err != nil {
			return nil, false, err
		}
		pods, err := client.CoreV1().Pods(scope.Namespace).List(ctx, metav1.ListOptions{Limit: MaxObjects + 1})
		if err != nil {
			return nil, false, err
		}
		records := make([]Record, 0, len(list.Items))
		for _, item := range list.Items {
			records = append(records, projectReplicaSet(item, pods.Items))
		}
		return trim(records)
	case "services":
		list, err := client.CoreV1().Services(scope.Namespace).List(ctx, options)
		if err != nil {
			return nil, false, err
		}
		pods, err := client.CoreV1().Pods(scope.Namespace).List(ctx, metav1.ListOptions{Limit: MaxObjects + 1})
		if err != nil {
			return nil, false, err
		}
		slices, err := client.DiscoveryV1().EndpointSlices(scope.Namespace).List(ctx, metav1.ListOptions{Limit: MaxObjects + 1})
		if err != nil {
			return nil, false, err
		}
		records := make([]Record, 0, len(list.Items))
		for _, item := range list.Items {
			records = append(records, projectService(item, pods.Items, slices.Items))
		}
		return trim(records)
	case "endpointslices":
		list, err := client.DiscoveryV1().EndpointSlices(scope.Namespace).List(ctx, options)
		if err != nil {
			return nil, false, err
		}
		records := make([]Record, 0, len(list.Items))
		for _, item := range list.Items {
			records = append(records, projectEndpointSlice(item))
		}
		return trim(records)
	default:
		return nil, false, errors.New("unsupported resource")
	}
}

func projectNode(item corev1.Node) Record {
	ready := "Unknown"
	for _, condition := range item.Status.Conditions {
		if condition.Type == corev1.NodeReady {
			ready = string(condition.Status)
		}
	}
	roles := make([]string, 0)
	for key := range item.Labels {
		if strings.HasPrefix(key, "node-role.kubernetes.io/") {
			roles = append(roles, strings.TrimPrefix(key, "node-role.kubernetes.io/"))
		}
	}
	sort.Strings(roles)
	return Record{Kind: "Node", Name: item.Name, Status: "Ready=" + ready, Fields: []Field{
		{Label: "Roles", Value: strings.Join(roles, ", ")}, {Label: "Scheduling", Value: strconv.FormatBool(item.Spec.Unschedulable)},
		{Label: "Kubelet", Value: item.Status.NodeInfo.KubeletVersion}, {Label: "CPU", Value: item.Status.Capacity.Cpu().String()},
		{Label: "Memory", Value: item.Status.Capacity.Memory().String()}, {Label: "Pods", Value: item.Status.Capacity.Pods().String()},
	}}
}

func projectPod(item corev1.Pod) Record {
	ready, restarts := 0, int32(0)
	containers := make([]string, 0, len(item.Spec.Containers))
	for _, container := range item.Spec.Containers {
		containers = append(containers, container.Name)
	}
	for _, status := range item.Status.ContainerStatuses {
		if status.Ready {
			ready++
		}
		restarts += status.RestartCount
	}
	return Record{Kind: "Pod", Name: item.Name, Namespace: item.Namespace, Status: string(item.Status.Phase), Owners: owners(item.Namespace, item.OwnerReferences), Fields: []Field{
		{Label: "Ready", Value: fmt.Sprintf("%d/%d", ready, len(item.Spec.Containers))}, {Label: "Restarts", Value: strconv.Itoa(int(restarts))},
		{Label: "Node", Value: item.Spec.NodeName}, {Label: "Containers", Value: strings.Join(containers, ", ")},
	}}
}

func selectedPods(namespace string, selector *metav1.LabelSelector, pods []corev1.Pod) []Reference {
	parsed, err := metav1.LabelSelectorAsSelector(selector)
	if err != nil || parsed.Empty() {
		return nil
	}
	result := make([]Reference, 0)
	for _, pod := range pods {
		if parsed.Matches(labels.Set(pod.Labels)) {
			result = append(result, Reference{Kind: "Pod", Name: pod.Name, Namespace: namespace, Relation: "selects"})
		}
		if len(result) == MaxObjects {
			break
		}
	}
	return result
}

func projectDeployment(item appsv1.Deployment, pods []corev1.Pod) Record {
	selector, _ := metav1.LabelSelectorAsSelector(item.Spec.Selector)
	return Record{Kind: "Deployment", Name: item.Name, Namespace: item.Namespace, Status: fmt.Sprintf("%d/%d ready", item.Status.ReadyReplicas, item.Status.Replicas), Owners: owners(item.Namespace, item.OwnerReferences), Related: selectedPods(item.Namespace, item.Spec.Selector, pods), Fields: []Field{
		{Label: "Replicas", Value: fmt.Sprintf("desired %d · current %d · ready %d · available %d", value(item.Spec.Replicas), item.Status.Replicas, item.Status.ReadyReplicas, item.Status.AvailableReplicas)},
		{Label: "Selector", Value: selector.String()},
	}}
}

func projectReplicaSet(item appsv1.ReplicaSet, pods []corev1.Pod) Record {
	selector, _ := metav1.LabelSelectorAsSelector(item.Spec.Selector)
	return Record{Kind: "ReplicaSet", Name: item.Name, Namespace: item.Namespace, Status: fmt.Sprintf("%d/%d ready", item.Status.ReadyReplicas, item.Status.Replicas), Owners: owners(item.Namespace, item.OwnerReferences), Related: selectedPods(item.Namespace, item.Spec.Selector, pods), Fields: []Field{
		{Label: "Replicas", Value: fmt.Sprintf("desired %d · current %d · ready %d · available %d", value(item.Spec.Replicas), item.Status.Replicas, item.Status.ReadyReplicas, item.Status.AvailableReplicas)},
		{Label: "Selector", Value: selector.String()},
	}}
}

func projectService(item corev1.Service, pods []corev1.Pod, slices []discoveryv1.EndpointSlice) Record {
	selector := labels.Set(item.Spec.Selector).AsSelector()
	ports := make([]string, 0, len(item.Spec.Ports))
	for _, port := range item.Spec.Ports {
		ports = append(ports, fmt.Sprintf("%s %d/%s", port.Name, port.Port, port.Protocol))
	}
	related := make([]Reference, 0)
	if len(item.Spec.Selector) > 0 {
		for _, pod := range pods {
			if selector.Matches(labels.Set(pod.Labels)) {
				related = append(related, Reference{Kind: "Pod", Name: pod.Name, Namespace: item.Namespace, Relation: "selects"})
			}
		}
	}
	for _, slice := range slices {
		if slice.Labels[discoveryv1.LabelServiceName] == item.Name {
			related = append(related, Reference{Kind: "EndpointSlice", Name: slice.Name, Namespace: item.Namespace, Relation: "routes-via"})
		}
	}
	if len(related) > MaxObjects {
		related = related[:MaxObjects]
	}
	return Record{Kind: "Service", Name: item.Name, Namespace: item.Namespace, Status: string(item.Spec.Type), Owners: owners(item.Namespace, item.OwnerReferences), Related: related, Fields: []Field{
		{Label: "Type", Value: string(item.Spec.Type)}, {Label: "Ports", Value: strings.Join(ports, ", ")}, {Label: "Selector", Value: selector.String()},
	}}
}

func projectEndpointSlice(item discoveryv1.EndpointSlice) Record {
	ports := make([]string, 0, len(item.Ports))
	for _, port := range item.Ports {
		name, number, protocol := "", "", ""
		if port.Name != nil {
			name = *port.Name
		}
		if port.Port != nil {
			number = strconv.Itoa(int(*port.Port))
		}
		if port.Protocol != nil {
			protocol = string(*port.Protocol)
		}
		ports = append(ports, strings.TrimSpace(name+" "+number+"/"+protocol))
	}
	ready := 0
	for _, endpoint := range item.Endpoints {
		if endpoint.Conditions.Ready != nil && *endpoint.Conditions.Ready {
			ready++
		}
	}
	related := []Reference{}
	if serviceName := item.Labels[discoveryv1.LabelServiceName]; serviceName != "" {
		related = append(related, Reference{Kind: "Service", Name: serviceName, Namespace: item.Namespace, Relation: "serves"})
	}
	return Record{Kind: "EndpointSlice", Name: item.Name, Namespace: item.Namespace, Status: fmt.Sprintf("%d/%d ready", ready, len(item.Endpoints)), Owners: owners(item.Namespace, item.OwnerReferences), Related: related, Fields: []Field{
		{Label: "Address type", Value: string(item.AddressType)}, {Label: "Ports", Value: strings.Join(ports, ", ")}, {Label: "Ready endpoints", Value: fmt.Sprintf("%d/%d", ready, len(item.Endpoints))},
	}}
}

func value(pointer *int32) int32 {
	if pointer == nil {
		return 0
	}
	return *pointer
}
