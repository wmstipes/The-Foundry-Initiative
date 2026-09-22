package main

import (
	"context"
	"errors"
	"flag"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"os/signal"
	"strings"
	"syscall"
	"time"

	appsv1 "k8s.io/api/apps/v1"
	corev1 "k8s.io/api/core/v1"
	discoveryv1 "k8s.io/api/discovery/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/apimachinery/pkg/types"
	"k8s.io/apimachinery/pkg/util/intstr"
	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/kubernetes/fake"
	clientcmdapi "k8s.io/client-go/tools/clientcmd/api"

	console "github.com/wmstipes/The-Foundry-Initiative/apps/forgeops-console"
	"github.com/wmstipes/The-Foundry-Initiative/apps/forgeops-console/internal/broker"
	"github.com/wmstipes/The-Foundry-Initiative/apps/forgeops-console/internal/cluster"
	"github.com/wmstipes/The-Foundry-Initiative/apps/forgeops-console/internal/config"
	"github.com/wmstipes/The-Foundry-Initiative/apps/forgeops-console/internal/diagnostics"
	"github.com/wmstipes/The-Foundry-Initiative/apps/forgeops-console/internal/plugins"
	"github.com/wmstipes/The-Foundry-Initiative/apps/forgeops-console/internal/resources"
	"github.com/wmstipes/The-Foundry-Initiative/apps/forgeops-console/internal/server"
	"github.com/wmstipes/The-Foundry-Initiative/apps/forgeops-console/internal/session"
)

func main() {
	if err := run(); err != nil {
		log.Printf("ForgeOps Console demo stopped: %v", err)
		os.Exit(1)
	}
}

func run() error {
	listenAddress := flag.String("listen", "127.0.0.1:9090", "literal loopback listen address")
	webDirectory := flag.String("web-dir", "", "path to the built browser assets")
	buildInfo := flag.Bool("build-info", false, "print build identity without loading configuration or starting a listener")
	scenario := flag.String("scenario", "default", "synthetic data set: default, routing-before, or routing-after")
	flag.Parse()
	if *buildInfo {
		return console.PrintBuildInfo()
	}
	if *webDirectory == "" {
		return errors.New("--web-dir is required")
	}
	if err := server.ValidateListenAddress(*listenAddress); err != nil {
		return err
	}
	contextName, objects, err := scenarioObjects(*scenario)
	if err != nil {
		return err
	}
	raw := demoConfig(contextName)
	state, err := session.New([]string{contextName})
	if err != nil {
		return err
	}
	nonce, err := session.NewNonce()
	if err != nil {
		return fmt.Errorf("create session nonce: %w", err)
	}
	registry, err := plugins.NewRegistry(plugins.ExampleManifest(), plugins.ResourcesManifest(), plugins.DiagnosticsManifest())
	if err != nil {
		return err
	}
	capabilityBroker, err := broker.New(registry)
	if err != nil {
		return err
	}
	var eventPod *corev1.Pod
	for _, object := range objects {
		if pod, ok := object.(*corev1.Pod); ok {
			pod.UID = types.UID("demo-" + pod.Name)
			if eventPod == nil {
				eventPod = pod
			}
		}
	}
	if eventPod != nil {
		objects = append(objects, &corev1.Event{ObjectMeta: metav1.ObjectMeta{Name: "synthetic-started", Namespace: eventPod.Namespace}, InvolvedObject: corev1.ObjectReference{Kind: "Pod", Name: eventPod.Name, Namespace: eventPod.Namespace, UID: eventPod.UID}, Type: "Normal", Reason: "Started", Message: "Synthetic example: container started; no cluster connection.", Count: 1})
	}
	client := fake.NewSimpleClientset(objects...)
	factory := cluster.ClientFactoryFunc(func(context.Context, *clientcmdapi.Config, string) (kubernetes.Interface, error) { return client, nil })
	resourceService, err := resources.New(raw, state, factory)
	if err != nil {
		return err
	}
	if err := capabilityBroker.Register(plugins.ExamplePluginID, plugins.ExampleStatusCapability, func(context.Context, broker.Request) (broker.Response, error) {
		return broker.Response{Message: "Synthetic data only; no cluster connection exists.", Mode: "synthetic-demo"}, nil
	}); err != nil {
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
	diagnosticService, err := diagnostics.New(raw, state, factory, func(context.Context, kubernetes.Interface, string, string, *corev1.PodLogOptions) (io.ReadCloser, error) {
		return io.NopCloser(strings.NewReader("SYNTHETIC LOG — no cluster connection\nGET /healthz 200\nExample terminal control: \x1b[31m rendered as inert text\n")), nil
	}, resourceService.RecordDiagnostic)
	if err != nil {
		return err
	}
	if err = capabilityBroker.RegisterDiagnostics(diagnosticService); err != nil {
		return err
	}
	handler, err := server.New(server.Options{
		AllowedHost: *listenAddress,
		Contexts:    []config.ContextSummary{{Name: contextName, ClusterName: "synthetic", AuthInfoName: "none"}},
		State:       state, Registry: registry, Broker: capabilityBroker, Resources: resourceService,
		Static: os.DirFS(*webDirectory), Nonce: nonce, Mode: "synthetic-demo",
	})
	if err != nil {
		return err
	}
	httpServer := &http.Server{Addr: *listenAddress, Handler: handler, ReadHeaderTimeout: 5 * time.Second, ReadTimeout: 10 * time.Second, WriteTimeout: 15 * time.Second, IdleTimeout: 30 * time.Second}
	shutdownContext, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()

	log.Printf("ForgeOps Console demo at http://%s (synthetic scenario %s; no cluster connection)", *listenAddress, *scenario)
	return server.ListenAndServe(shutdownContext, httpServer, state)
}

func scenarioObjects(scenario string) (string, []runtime.Object, error) {
	switch scenario {
	case "default":
		return "synthetic-demo", demoObjects(), nil
	case "routing-before":
		return "synthetic-routing-before", routingRegressionObjects(false), nil
	case "routing-after":
		return "synthetic-routing-after", routingRegressionObjects(true), nil
	default:
		return "", nil, errors.New("unsupported synthetic scenario")
	}
}

func demoConfig(contextName string) *clientcmdapi.Config {
	return &clientcmdapi.Config{
		Contexts:  map[string]*clientcmdapi.Context{contextName: {Cluster: "synthetic", AuthInfo: "none"}},
		Clusters:  map[string]*clientcmdapi.Cluster{"synthetic": {Server: "https://synthetic.invalid", CertificateAuthorityData: []byte("synthetic")}},
		AuthInfos: map[string]*clientcmdapi.AuthInfo{"none": {}},
	}
}

// routingRegressionObjects deliberately shares the fixture's Service name,
// namespace and endpoint counts, but is independent synthetic Kubernetes data.
func routingRegressionObjects(after bool) []runtime.Object {
	const namespace = "forge-restaurant"
	const serviceName = "synthetic-service"
	replicas := int32(3)
	controller := true
	portName := "http"
	port := int32(8000)
	protocol := corev1.ProtocolTCP
	deploymentUID := typesUID("synthetic-restaurant-deployment")
	rsUID := typesUID("synthetic-restaurant-replicaset")
	objects := []runtime.Object{
		&corev1.Namespace{ObjectMeta: metav1.ObjectMeta{Name: namespace}, Status: corev1.NamespaceStatus{Phase: corev1.NamespaceActive}},
		&appsv1.Deployment{ObjectMeta: metav1.ObjectMeta{Name: "restaurant-api", Namespace: namespace, UID: deploymentUID}, Spec: appsv1.DeploymentSpec{Replicas: &replicas, Selector: &metav1.LabelSelector{MatchLabels: map[string]string{"app": "restaurant-api"}}}, Status: appsv1.DeploymentStatus{Replicas: 3, ReadyReplicas: 3, AvailableReplicas: 3}},
		&appsv1.ReplicaSet{ObjectMeta: metav1.ObjectMeta{Name: "restaurant-api-demo", Namespace: namespace, UID: rsUID, OwnerReferences: []metav1.OwnerReference{{APIVersion: "apps/v1", Kind: "Deployment", Name: "restaurant-api", UID: deploymentUID, Controller: &controller}}}, Spec: appsv1.ReplicaSetSpec{Replicas: &replicas, Selector: &metav1.LabelSelector{MatchLabels: map[string]string{"app": "restaurant-api"}}}, Status: appsv1.ReplicaSetStatus{Replicas: 3, ReadyReplicas: 3, AvailableReplicas: 3}},
	}
	for i := 1; i <= 3; i++ {
		objects = append(objects, &corev1.Pod{ObjectMeta: metav1.ObjectMeta{Name: fmt.Sprintf("restaurant-api-demo-%d", i), Namespace: namespace, Labels: map[string]string{"app": "restaurant-api"}, OwnerReferences: []metav1.OwnerReference{{APIVersion: "apps/v1", Kind: "ReplicaSet", Name: "restaurant-api-demo", UID: rsUID, Controller: &controller}}}, Spec: corev1.PodSpec{Containers: []corev1.Container{{Name: "api", Image: "synthetic/restaurant-api:demo"}}}, Status: corev1.PodStatus{Phase: corev1.PodRunning, ContainerStatuses: []corev1.ContainerStatus{{Name: "api", Ready: true}}}})
	}
	objects = append(objects, &corev1.Service{ObjectMeta: metav1.ObjectMeta{Name: serviceName, Namespace: namespace}, Spec: corev1.ServiceSpec{Type: corev1.ServiceTypeClusterIP, Selector: map[string]string{"app": "restaurant-api"}, Ports: []corev1.ServicePort{{Name: portName, Port: 80, Protocol: protocol, TargetPort: intstr.FromInt32(port)}}}})
	endpoints := make([]discoveryv1.Endpoint, 3)
	for i := range endpoints {
		endpoints[i] = discoveryv1.Endpoint{Addresses: []string{fmt.Sprintf("192.0.2.%d", i+1)}, Conditions: discoveryv1.EndpointConditions{Ready: boolPointer(!after || i < 2)}}
	}
	objects = append(objects, &discoveryv1.EndpointSlice{ObjectMeta: metav1.ObjectMeta{Name: "synthetic-service-demo", Namespace: namespace, Labels: map[string]string{discoveryv1.LabelServiceName: serviceName}}, AddressType: discoveryv1.AddressTypeIPv4, Ports: []discoveryv1.EndpointPort{{Name: &portName, Port: &port, Protocol: &protocol}}, Endpoints: endpoints})
	return objects
}

func demoObjects() []runtime.Object {
	replicas := int32(3)
	controller := true
	ready := true
	serviceName := "signalforge-api"
	portName := "http"
	port := int32(8000)
	protocol := corev1.ProtocolTCP
	deploymentUID := "demo-deployment"
	rsUID := "demo-replicaset"
	return []runtime.Object{
		&corev1.Namespace{ObjectMeta: metav1.ObjectMeta{Name: "signalforge"}, Status: corev1.NamespaceStatus{Phase: corev1.NamespaceActive}},
		&corev1.Namespace{ObjectMeta: metav1.ObjectMeta{Name: "observability"}, Status: corev1.NamespaceStatus{Phase: corev1.NamespaceActive}},
		&corev1.Node{ObjectMeta: metav1.ObjectMeta{Name: "forge-control-1", Labels: map[string]string{"node-role.kubernetes.io/control-plane": ""}}, Status: corev1.NodeStatus{Conditions: []corev1.NodeCondition{{Type: corev1.NodeReady, Status: corev1.ConditionTrue}}, NodeInfo: corev1.NodeSystemInfo{KubeletVersion: "v1.34.0"}}},
		&appsv1.Deployment{ObjectMeta: metav1.ObjectMeta{Name: "signalforge-api", Namespace: "signalforge", UID: typesUID(deploymentUID)}, Spec: appsv1.DeploymentSpec{Replicas: &replicas, Selector: &metav1.LabelSelector{MatchLabels: map[string]string{"app": "signalforge-api"}}}, Status: appsv1.DeploymentStatus{Replicas: 3, ReadyReplicas: 2, AvailableReplicas: 2}},
		&appsv1.ReplicaSet{ObjectMeta: metav1.ObjectMeta{Name: "signalforge-api-7f8b9", Namespace: "signalforge", UID: typesUID(rsUID), OwnerReferences: []metav1.OwnerReference{{APIVersion: "apps/v1", Kind: "Deployment", Name: "signalforge-api", UID: typesUID(deploymentUID), Controller: &controller}}}, Spec: appsv1.ReplicaSetSpec{Replicas: &replicas, Selector: &metav1.LabelSelector{MatchLabels: map[string]string{"app": "signalforge-api"}}}, Status: appsv1.ReplicaSetStatus{Replicas: 3, ReadyReplicas: 2, AvailableReplicas: 2}},
		&corev1.Pod{ObjectMeta: metav1.ObjectMeta{Name: "signalforge-api-7f8b9-a1", Namespace: "signalforge", Labels: map[string]string{"app": "signalforge-api"}, OwnerReferences: []metav1.OwnerReference{{APIVersion: "apps/v1", Kind: "ReplicaSet", Name: "signalforge-api-7f8b9", UID: typesUID(rsUID), Controller: &controller}}}, Spec: corev1.PodSpec{NodeName: "forge-control-1", Containers: []corev1.Container{{Name: "api", Image: "synthetic/signalforge:demo"}}}, Status: corev1.PodStatus{Phase: corev1.PodRunning, ContainerStatuses: []corev1.ContainerStatus{{Name: "api", Ready: true}}}},
		&corev1.Pod{ObjectMeta: metav1.ObjectMeta{Name: "signalforge-api-7f8b9-b2", Namespace: "signalforge", Labels: map[string]string{"app": "signalforge-api"}, OwnerReferences: []metav1.OwnerReference{{APIVersion: "apps/v1", Kind: "ReplicaSet", Name: "signalforge-api-7f8b9", UID: typesUID(rsUID), Controller: &controller}}}, Spec: corev1.PodSpec{NodeName: "forge-control-1", Containers: []corev1.Container{{Name: "api", Image: "synthetic/signalforge:demo"}}}, Status: corev1.PodStatus{Phase: corev1.PodPending, ContainerStatuses: []corev1.ContainerStatus{{Name: "api", Ready: false, RestartCount: 2}}}},
		&corev1.Service{ObjectMeta: metav1.ObjectMeta{Name: serviceName, Namespace: "signalforge"}, Spec: corev1.ServiceSpec{Type: corev1.ServiceTypeClusterIP, Selector: map[string]string{"app": "signalforge-api"}, Ports: []corev1.ServicePort{{Name: portName, Port: 80, Protocol: protocol, TargetPort: intstr.FromInt32(port)}}}},
		&discoveryv1.EndpointSlice{ObjectMeta: metav1.ObjectMeta{Name: "signalforge-api-demo", Namespace: "signalforge", Labels: map[string]string{discoveryv1.LabelServiceName: serviceName}}, AddressType: discoveryv1.AddressTypeIPv4, Ports: []discoveryv1.EndpointPort{{Name: &portName, Port: &port, Protocol: &protocol}}, Endpoints: []discoveryv1.Endpoint{{Addresses: []string{"10.42.0.8"}, Conditions: discoveryv1.EndpointConditions{Ready: &ready}}, {Addresses: []string{"10.42.0.9"}, Conditions: discoveryv1.EndpointConditions{Ready: boolPointer(false)}}}},
	}
}

func boolPointer(value bool) *bool    { return &value }
func typesUID(value string) types.UID { return types.UID(value) }
