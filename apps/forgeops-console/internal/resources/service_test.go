package resources

import (
	"context"
	"errors"
	"fmt"
	"testing"

	appsv1 "k8s.io/api/apps/v1"
	corev1 "k8s.io/api/core/v1"
	discoveryv1 "k8s.io/api/discovery/v1"
	apierrors "k8s.io/apimachinery/pkg/api/errors"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/apimachinery/pkg/runtime/schema"
	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/kubernetes/fake"
	clienttesting "k8s.io/client-go/testing"
	clientcmdapi "k8s.io/client-go/tools/clientcmd/api"

	"github.com/wmstipes/The-Foundry-Initiative/apps/forgeops-console/internal/cluster"
	"github.com/wmstipes/The-Foundry-Initiative/apps/forgeops-console/internal/session"
)

func fixture(t *testing.T, objects ...runtime.Object) (*Service, *session.State, *fake.Clientset) {
	t.Helper()
	state, err := session.New([]string{"dev"})
	if err != nil {
		t.Fatal(err)
	}
	client := fake.NewSimpleClientset(objects...)
	raw := &clientcmdapi.Config{Contexts: map[string]*clientcmdapi.Context{"dev": {Cluster: "cluster", AuthInfo: "user"}}}
	service, err := New(raw, state, cluster.ClientFactoryFunc(func(context.Context, *clientcmdapi.Config, string) (kubernetes.Interface, error) { return client, nil }))
	if err != nil {
		t.Fatal(err)
	}
	return service, state, client
}

func selectNamespace(t *testing.T, service *Service, state *session.State, name string) session.Scope {
	t.Helper()
	scope, err := state.SelectContext("dev")
	if err != nil {
		t.Fatal(err)
	}
	if _, err := service.Execute(context.Background(), Query{Generation: scope.Generation, Operation: "list", Resource: "namespaces"}); err != nil {
		t.Fatal(err)
	}
	scope, err = state.SelectNamespace(name)
	if err != nil {
		t.Fatal(err)
	}
	return scope
}

func TestFixedProjectionAndRelationshipsExcludeRawMetadata(t *testing.T) {
	replicas := int32(2)
	service, state, _ := fixture(t,
		&corev1.Namespace{ObjectMeta: metav1.ObjectMeta{Name: "team"}, Status: corev1.NamespaceStatus{Phase: corev1.NamespaceActive}},
		&appsv1.Deployment{ObjectMeta: metav1.ObjectMeta{Name: "api", Namespace: "team", Annotations: map[string]string{"secret.example/token": "must-not-escape"}}, Spec: appsv1.DeploymentSpec{Replicas: &replicas, Selector: &metav1.LabelSelector{MatchLabels: map[string]string{"app": "api"}}}, Status: appsv1.DeploymentStatus{Replicas: 2, ReadyReplicas: 1}},
		&corev1.Pod{ObjectMeta: metav1.ObjectMeta{Name: "api-one", Namespace: "team", Labels: map[string]string{"app": "api"}}, Spec: corev1.PodSpec{Containers: []corev1.Container{{Name: "api"}}}, Status: corev1.PodStatus{Phase: corev1.PodRunning}},
	)
	scope := selectNamespace(t, service, state, "team")
	result, err := service.Execute(context.Background(), Query{Generation: scope.Generation, Operation: "list", Resource: "deployments"})
	if err != nil {
		t.Fatal(err)
	}
	if len(result.Items) != 1 || len(result.Items[0].Related) != 1 || result.Items[0].Related[0].Name != "api-one" {
		t.Fatalf("unexpected projection %#v", result)
	}
	for _, field := range result.Items[0].Fields {
		if field.Value == "must-not-escape" {
			t.Fatal("annotation value escaped projection")
		}
	}
}

func TestRejectsArbitraryAndStaleQueries(t *testing.T) {
	service, state, _ := fixture(t, &corev1.Namespace{ObjectMeta: metav1.ObjectMeta{Name: "team"}})
	scope := selectNamespace(t, service, state, "team")
	for _, query := range []Query{
		{Generation: scope.Generation, Operation: "delete", Resource: "pods"},
		{Generation: scope.Generation, Operation: "list", Resource: "secrets"},
		{Generation: scope.Generation, Operation: "list", Resource: "pods", Name: "unexpected"},
	} {
		var apiError *APIError
		if _, err := service.Execute(context.Background(), query); !errors.As(err, &apiError) || apiError.Code != "invalid_request" {
			t.Fatalf("expected invalid request for %#v, got %v", query, err)
		}
	}
	if _, err := state.SelectContext("dev"); err != nil {
		t.Fatal(err)
	}
	var apiError *APIError
	if _, err := service.Execute(context.Background(), Query{Generation: scope.Generation, Operation: "list", Resource: "pods"}); !errors.As(err, &apiError) || apiError.Code != "stale_scope" {
		t.Fatalf("expected stale scope, got %v", err)
	}
}

func TestObjectAndActivityLimitsAreBounded(t *testing.T) {
	objects := []runtime.Object{&corev1.Namespace{ObjectMeta: metav1.ObjectMeta{Name: "team"}}}
	for index := 0; index < MaxObjects+5; index++ {
		objects = append(objects, &corev1.Pod{ObjectMeta: metav1.ObjectMeta{Name: fmt.Sprintf("pod-%03d", index), Namespace: "team"}})
	}
	service, state, _ := fixture(t, objects...)
	scope := selectNamespace(t, service, state, "team")
	for index := 0; index < MaxActivity+5; index++ {
		result, err := service.Execute(context.Background(), Query{Generation: scope.Generation, Operation: "list", Resource: "pods"})
		if err != nil {
			t.Fatal(err)
		}
		if len(result.Items) != MaxObjects || !result.Truncated {
			t.Fatalf("result was not bounded: %d %#v", len(result.Items), result)
		}
	}
	if count := len(service.Activity()); count != MaxActivity {
		t.Fatalf("activity count = %d", count)
	}
}

func TestForbiddenErrorIsSanitized(t *testing.T) {
	service, state, client := fixture(t, &corev1.Namespace{ObjectMeta: metav1.ObjectMeta{Name: "team"}})
	scope := selectNamespace(t, service, state, "team")
	client.PrependReactor("list", "pods", func(clienttesting.Action) (bool, runtime.Object, error) {
		return true, nil, apierrors.NewForbidden(schema.GroupResource{Resource: "pods"}, "private-pod", errors.New("credential-bearing upstream detail"))
	})
	var apiError *APIError
	if _, err := service.Execute(context.Background(), Query{Generation: scope.Generation, Operation: "list", Resource: "pods"}); !errors.As(err, &apiError) || apiError.Code != "forbidden" || apiError.Error() != "forbidden" {
		t.Fatalf("unexpected mapped error %v", err)
	}
}

func TestRelationshipCompletenessSurvivesListAndRead(t *testing.T) {
	for _, resource := range []string{"deployments", "replicasets", "services"} {
		for _, operation := range []string{"list", "read"} {
			for _, mode := range []string{"pod-page", "pod-limit", "slice-page", "combined-limit", "complete"} {
				if resource != "services" && (mode == "slice-page" || mode == "combined-limit") {
					continue
				}
				t.Run(resource+"/"+operation+"/"+mode, func(t *testing.T) {
					selector := &metav1.LabelSelector{MatchLabels: map[string]string{"app": "api"}}
					objects := []runtime.Object{&corev1.Namespace{ObjectMeta: metav1.ObjectMeta{Name: "team"}},
						&appsv1.Deployment{ObjectMeta: metav1.ObjectMeta{Name: "api", Namespace: "team"}, Spec: appsv1.DeploymentSpec{Selector: selector}},
						&appsv1.ReplicaSet{ObjectMeta: metav1.ObjectMeta{Name: "api", Namespace: "team"}, Spec: appsv1.ReplicaSetSpec{Selector: selector}},
						&corev1.Service{ObjectMeta: metav1.ObjectMeta{Name: "api", Namespace: "team"}, Spec: corev1.ServiceSpec{Selector: map[string]string{"app": "api"}}},
					}
					count := 1
					if mode == "pod-limit" {
						count = MaxObjects + 1
					}
					if mode == "combined-limit" {
						count = MaxObjects
					}
					for i := 0; i < count; i++ {
						objects = append(objects, &corev1.Pod{ObjectMeta: metav1.ObjectMeta{Name: fmt.Sprintf("pod-%03d", i), Namespace: "team", Labels: map[string]string{"app": "api"}}})
					}
					if mode == "combined-limit" {
						objects = append(objects, &discoveryv1.EndpointSlice{ObjectMeta: metav1.ObjectMeta{Name: "slice", Namespace: "team", Labels: map[string]string{discoveryv1.LabelServiceName: "api"}}})
					}
					service, state, client := fixture(t, objects...)
					scope := selectNamespace(t, service, state, "team")
					if mode == "pod-page" {
						client.PrependReactor("list", "pods", func(clienttesting.Action) (bool, runtime.Object, error) {
							return true, &corev1.PodList{ListMeta: metav1.ListMeta{Continue: "next"}}, nil
						})
					}
					if mode == "slice-page" {
						client.PrependReactor("list", "endpointslices", func(clienttesting.Action) (bool, runtime.Object, error) {
							return true, &discoveryv1.EndpointSliceList{ListMeta: metav1.ListMeta{Continue: "next"}}, nil
						})
					}
					query := Query{Generation: scope.Generation, Operation: operation, Resource: resource}
					if operation == "read" {
						query.Name = "api"
					}
					got, err := service.Execute(context.Background(), query)
					if err != nil {
						t.Fatal(err)
					}
					if len(got.Items) != 1 || got.Truncated != (mode != "complete") || len(got.Items[0].Related) > MaxObjects {
						t.Fatalf("incorrect completeness: %#v", got)
					}
				})
			}
		}
	}
}

func TestPrimaryPaginationAndLateCancellation(t *testing.T) {
	for _, mode := range []string{"page", "cancel"} {
		t.Run(mode, func(t *testing.T) {
			service, state, client := fixture(t, &corev1.Namespace{ObjectMeta: metav1.ObjectMeta{Name: "team"}})
			scope := selectNamespace(t, service, state, "team")
			ctx, cancel := context.WithCancel(context.Background())
			defer cancel()
			client.PrependReactor("list", "pods", func(clienttesting.Action) (bool, runtime.Object, error) {
				if mode == "cancel" {
					cancel()
				}
				return true, &corev1.PodList{ListMeta: metav1.ListMeta{Continue: "next"}, Items: []corev1.Pod{{ObjectMeta: metav1.ObjectMeta{Name: "api", Namespace: "team"}}}}, nil
			})
			got, err := service.Execute(ctx, Query{Generation: scope.Generation, Operation: "list", Resource: "pods"})
			if mode == "page" && (err != nil || !got.Truncated) {
				t.Fatalf("page lost: %#v %v", got, err)
			}
			if mode == "cancel" && (err == nil || len(got.Items) != 0) {
				t.Fatalf("cancelled result escaped: %#v %v", got, err)
			}
		})
	}
}
