import sys
from pathlib import Path

import yaml

RESTAURANT_MANIFEST_DIR = Path("k8s/fastapi-restaurant")
PROMETHEUS_MANIFEST_DIR = Path("k8s/prometheus")
METRICS_SERVER_MANIFEST_DIR = Path("k8s/metrics-server")

RESTAURANT_NAMESPACE = "forge-restaurant"
RESTAURANT_APP = "restaurant-api"
EXPECTED_IMAGE_PREFIX = "wmstipes/signalforge-restaurant-api:"
EXPECTED_NODEPORT = 30080
EXPECTED_VERSION = "0.7.0"
EXPECTED_RESTAURANT_IMAGE = f"{EXPECTED_IMAGE_PREFIX}{EXPECTED_VERSION}"

PROMETHEUS_NAMESPACE = "forge-observability"
PROMETHEUS_APP = "prometheus"
PROMETHEUS_IMAGE = "prom/prometheus:v3.13.2"
PROMETHEUS_ROLE = "prometheus-restaurant-pod-reader"

METRICS_SERVER_NAMESPACE = "kube-system"
METRICS_SERVER_APP = "metrics-server"
METRICS_SERVER_IMAGE = "registry.k8s.io/metrics-server/metrics-server:v0.9.0"
METRICS_SERVER_CA_ARGUMENT = (
    "--kubelet-certificate-authority="
    "/var/run/secrets/kubernetes.io/serviceaccount/ca.crt"
)

REQUIRED_RESTAURANT_FILES = [
    "namespace.yaml",
    "restaurant-api-config.yaml",
    "restaurant-api-deployment.yaml",
    "restaurant-api-service.yaml",
    "restaurant-api-nodeport.yaml",
]

REQUIRED_PROMETHEUS_FILES = [
    "namespace.yaml",
    "prometheus-service-account.yaml",
    "restaurant-pod-reader-role.yaml",
    "restaurant-pod-reader-role-binding.yaml",
    "prometheus-config.yaml",
    "prometheus-deployment.yaml",
    "prometheus-service.yaml",
]

REQUIRED_METRICS_SERVER_FILES = [
    "metrics-server-service-account.yaml",
    "metrics-server-rbac.yaml",
    "metrics-server-service.yaml",
    "metrics-server-deployment.yaml",
    "metrics-server-api-service.yaml",
]


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    sys.exit(1)


def ok(message: str) -> None:
    print(f"OK: {message}")


def load_yaml(path: Path) -> dict:
    try:
        with path.open("r", encoding="utf-8-sig") as file:
            data = yaml.safe_load(file)
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        fail(f"{path} could not be parsed as YAML: {exc}")

    if not isinstance(data, dict):
        fail(f"{path} did not parse into a YAML object")

    return data


def load_yaml_documents(path: Path) -> list[dict]:
    try:
        with path.open("r", encoding="utf-8-sig") as file:
            documents = [document for document in yaml.safe_load_all(file) if document is not None]
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        fail(f"{path} could not be parsed as YAML: {exc}")

    require(documents, f"{path} did not contain any YAML objects")
    require(
        all(isinstance(document, dict) for document in documents),
        f"{path} contained a YAML document that was not an object",
    )
    return documents


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def require_files(directory: Path, filenames: list[str]) -> None:
    require(directory.exists(), f"{directory} does not exist")

    for filename in filenames:
        require((directory / filename).exists(), f"Missing required manifest: {directory / filename}")


def has_relabel_rule(
    rules: list[dict],
    source_label: str,
    *,
    action: str,
    regex: str | None = None,
    target_label: str | None = None,
) -> bool:
    for rule in rules:
        if rule.get("action") != action:
            continue
        if rule.get("source_labels") != [source_label]:
            continue
        if regex is not None and rule.get("regex") != regex:
            continue
        if target_label is not None and rule.get("target_label") != target_label:
            continue
        return True

    return False


def validate_restaurant_manifests() -> None:
    require_files(RESTAURANT_MANIFEST_DIR, REQUIRED_RESTAURANT_FILES)
    ok("All required Restaurant API manifest files exist")

    namespace = load_yaml(RESTAURANT_MANIFEST_DIR / "namespace.yaml")
    config = load_yaml(RESTAURANT_MANIFEST_DIR / "restaurant-api-config.yaml")
    deployment = load_yaml(RESTAURANT_MANIFEST_DIR / "restaurant-api-deployment.yaml")
    service = load_yaml(RESTAURANT_MANIFEST_DIR / "restaurant-api-service.yaml")
    nodeport = load_yaml(RESTAURANT_MANIFEST_DIR / "restaurant-api-nodeport.yaml")

    require(namespace.get("kind") == "Namespace", "Restaurant namespace manifest must be kind Namespace")
    require(namespace.get("metadata", {}).get("name") == RESTAURANT_NAMESPACE, "Restaurant namespace must be forge-restaurant")
    ok("Restaurant namespace manifest is valid")

    require(config.get("kind") == "ConfigMap", "restaurant-api-config.yaml must be kind ConfigMap")
    require(config.get("metadata", {}).get("namespace") == RESTAURANT_NAMESPACE, "Restaurant ConfigMap namespace mismatch")
    require(config.get("data", {}).get("APP_VERSION") == EXPECTED_VERSION, "ConfigMap APP_VERSION mismatch")
    require(config.get("data", {}).get("FEATURE_ANALYZE_ENABLED") == "true", "FEATURE_ANALYZE_ENABLED should be true")
    ok("Restaurant ConfigMap manifest is valid")

    require(deployment.get("kind") == "Deployment", "restaurant-api-deployment.yaml must be kind Deployment")
    require(deployment.get("metadata", {}).get("namespace") == RESTAURANT_NAMESPACE, "Restaurant Deployment namespace mismatch")
    require(deployment.get("metadata", {}).get("name") == RESTAURANT_APP, "Restaurant Deployment name mismatch")

    template = deployment.get("spec", {}).get("template", {})
    pod_labels = template.get("metadata", {}).get("labels", {})
    require(pod_labels.get("app") == RESTAURANT_APP, "Restaurant Deployment Pod label app mismatch")

    containers = template.get("spec", {}).get("containers", [])
    require(len(containers) == 1, "Restaurant Deployment should have exactly one container")

    container = containers[0]
    require(container.get("name") == RESTAURANT_APP, "Restaurant container name mismatch")
    require(container.get("image") == EXPECTED_RESTAURANT_IMAGE, "Restaurant container image/version mismatch")
    require("readinessProbe" in container, "Restaurant container missing readinessProbe")
    require("livenessProbe" in container, "Restaurant container missing livenessProbe")
    require("resources" in container, "Restaurant container missing resources block")
    ok("Restaurant Deployment manifest is valid")

    require(service.get("kind") == "Service", "restaurant-api-service.yaml must be kind Service")
    require(service.get("metadata", {}).get("namespace") == RESTAURANT_NAMESPACE, "Restaurant Service namespace mismatch")
    require(service.get("spec", {}).get("type") == "ClusterIP", "Restaurant internal Service must be ClusterIP")
    require(service.get("spec", {}).get("selector", {}).get("app") == RESTAURANT_APP, "Restaurant internal Service selector mismatch")
    ok("Restaurant internal Service manifest is valid")

    require(nodeport.get("kind") == "Service", "restaurant-api-nodeport.yaml must be kind Service")
    require(nodeport.get("metadata", {}).get("namespace") == RESTAURANT_NAMESPACE, "Restaurant NodePort Service namespace mismatch")
    require(nodeport.get("spec", {}).get("type") == "NodePort", "Restaurant external Service must be NodePort")
    require(nodeport.get("spec", {}).get("selector", {}).get("app") == RESTAURANT_APP, "Restaurant NodePort Service selector mismatch")

    ports = nodeport.get("spec", {}).get("ports", [])
    require(len(ports) == 1, "Restaurant NodePort Service should have one port entry")
    require(ports[0].get("nodePort") == EXPECTED_NODEPORT, "Restaurant NodePort must be 30080")
    ok("Restaurant NodePort Service manifest is valid")


def validate_prometheus_manifests() -> None:
    require_files(PROMETHEUS_MANIFEST_DIR, REQUIRED_PROMETHEUS_FILES)
    ok("All required Prometheus manifest files exist")

    namespace = load_yaml(PROMETHEUS_MANIFEST_DIR / "namespace.yaml")
    service_account = load_yaml(PROMETHEUS_MANIFEST_DIR / "prometheus-service-account.yaml")
    role = load_yaml(PROMETHEUS_MANIFEST_DIR / "restaurant-pod-reader-role.yaml")
    role_binding = load_yaml(PROMETHEUS_MANIFEST_DIR / "restaurant-pod-reader-role-binding.yaml")
    config_map = load_yaml(PROMETHEUS_MANIFEST_DIR / "prometheus-config.yaml")
    deployment = load_yaml(PROMETHEUS_MANIFEST_DIR / "prometheus-deployment.yaml")
    service = load_yaml(PROMETHEUS_MANIFEST_DIR / "prometheus-service.yaml")

    require(namespace.get("kind") == "Namespace", "Prometheus namespace manifest must be kind Namespace")
    require(namespace.get("metadata", {}).get("name") == PROMETHEUS_NAMESPACE, "Prometheus namespace must be forge-observability")
    ok("Prometheus namespace manifest is valid")

    require(service_account.get("kind") == "ServiceAccount", "Prometheus identity must be a ServiceAccount")
    require(service_account.get("metadata", {}).get("name") == PROMETHEUS_APP, "Prometheus ServiceAccount name mismatch")
    require(service_account.get("metadata", {}).get("namespace") == PROMETHEUS_NAMESPACE, "Prometheus ServiceAccount namespace mismatch")
    ok("Prometheus ServiceAccount manifest is valid")

    require(role.get("kind") == "Role", "Restaurant Pod reader must be a namespace-scoped Role")
    require(role.get("metadata", {}).get("name") == PROMETHEUS_ROLE, "Prometheus Role name mismatch")
    require(role.get("metadata", {}).get("namespace") == RESTAURANT_NAMESPACE, "Prometheus Role must be scoped to forge-restaurant")
    role_rules = role.get("rules", [])
    require(len(role_rules) == 1, "Prometheus Role should contain exactly one rule")
    require(role_rules[0].get("apiGroups") == [""], "Prometheus Role should use the core API group")
    require(role_rules[0].get("resources") == ["pods"], "Prometheus Role should grant access only to Pods")
    require(set(role_rules[0].get("verbs", [])) == {"get", "list", "watch"}, "Prometheus Role should grant only get, list, and watch")
    ok("Prometheus least-privilege Role manifest is valid")

    require(role_binding.get("kind") == "RoleBinding", "Prometheus access grant must be a RoleBinding")
    require(role_binding.get("metadata", {}).get("namespace") == RESTAURANT_NAMESPACE, "Prometheus RoleBinding must be scoped to forge-restaurant")
    require(role_binding.get("roleRef", {}).get("kind") == "Role", "Prometheus RoleBinding must reference a Role")
    require(role_binding.get("roleRef", {}).get("name") == PROMETHEUS_ROLE, "Prometheus RoleBinding roleRef mismatch")
    subjects = role_binding.get("subjects", [])
    require(len(subjects) == 1, "Prometheus RoleBinding should have exactly one subject")
    require(subjects[0].get("kind") == "ServiceAccount", "Prometheus RoleBinding subject must be a ServiceAccount")
    require(subjects[0].get("name") == PROMETHEUS_APP, "Prometheus RoleBinding subject name mismatch")
    require(subjects[0].get("namespace") == PROMETHEUS_NAMESPACE, "Prometheus RoleBinding subject namespace mismatch")
    ok("Prometheus RoleBinding manifest is valid")

    require(config_map.get("kind") == "ConfigMap", "prometheus-config.yaml must be kind ConfigMap")
    require(config_map.get("metadata", {}).get("namespace") == PROMETHEUS_NAMESPACE, "Prometheus ConfigMap namespace mismatch")
    prometheus_text = config_map.get("data", {}).get("prometheus.yml")
    require(isinstance(prometheus_text, str), "Prometheus ConfigMap must contain prometheus.yml")

    try:
        prometheus_config = yaml.safe_load(prometheus_text)
    except yaml.YAMLError as exc:
        fail(f"Embedded prometheus.yml could not be parsed: {exc}")

    global_config = prometheus_config.get("global", {})
    require(global_config.get("scrape_interval") == "30s", "Prometheus scrape interval must be 30s")
    require(global_config.get("scrape_timeout") == "10s", "Prometheus scrape timeout must be 10s")

    scrape_jobs = prometheus_config.get("scrape_configs", [])
    restaurant_jobs = [job for job in scrape_jobs if job.get("job_name") == RESTAURANT_APP]
    require(len(restaurant_jobs) == 1, "Prometheus must define exactly one restaurant-api scrape job")
    restaurant_job = restaurant_jobs[0]
    require(restaurant_job.get("metrics_path") == "/metrics", "Restaurant API metrics path must be /metrics")

    discovery = restaurant_job.get("kubernetes_sd_configs", [])
    require(len(discovery) == 1, "Restaurant API scrape job should have one Kubernetes discovery configuration")
    require(discovery[0].get("role") == "pod", "Restaurant API scrape job must use Pod discovery")
    require(discovery[0].get("namespaces", {}).get("names") == [RESTAURANT_NAMESPACE], "Prometheus Pod discovery must be limited to forge-restaurant")

    relabel_rules = restaurant_job.get("relabel_configs", [])
    required_keep_rules = {
        "__meta_kubernetes_pod_label_app": RESTAURANT_APP,
        "__meta_kubernetes_pod_container_name": RESTAURANT_APP,
        "__meta_kubernetes_pod_container_port_name": "http",
    }

    for source_label, regex in required_keep_rules.items():
        require(
            has_relabel_rule(relabel_rules, source_label, action="keep", regex=regex),
            f"Prometheus scrape job missing keep rule for {source_label}",
        )

    required_target_labels = {
        "__meta_kubernetes_namespace": "namespace",
        "__meta_kubernetes_pod_name": "pod",
        "__meta_kubernetes_pod_node_name": "node",
        "__meta_kubernetes_pod_phase": "pod_phase",
        "__meta_kubernetes_pod_ready": "pod_ready",
    }

    for source_label, target_label in required_target_labels.items():
        require(
            has_relabel_rule(relabel_rules, source_label, action="replace", target_label=target_label),
            f"Prometheus scrape job missing target label {target_label}",
        )

    ok("Prometheus scrape configuration is valid")

    require(deployment.get("kind") == "Deployment", "prometheus-deployment.yaml must be kind Deployment")
    require(deployment.get("metadata", {}).get("name") == PROMETHEUS_APP, "Prometheus Deployment name mismatch")
    require(deployment.get("metadata", {}).get("namespace") == PROMETHEUS_NAMESPACE, "Prometheus Deployment namespace mismatch")
    require(deployment.get("spec", {}).get("replicas") == 1, "Prometheus must use one replica")

    pod_spec = deployment.get("spec", {}).get("template", {}).get("spec", {})
    require(pod_spec.get("serviceAccountName") == PROMETHEUS_APP, "Prometheus Deployment ServiceAccount mismatch")
    containers = pod_spec.get("containers", [])
    require(len(containers) == 1, "Prometheus Deployment should have exactly one container")
    container = containers[0]
    require(container.get("name") == PROMETHEUS_APP, "Prometheus container name mismatch")
    require(container.get("image") == PROMETHEUS_IMAGE, "Prometheus image must be pinned to the approved version")
    require("--storage.tsdb.retention.time=48h" in container.get("args", []), "Prometheus retention time must be 48h")
    require("--storage.tsdb.retention.size=750MB" in container.get("args", []), "Prometheus retention size must be 750MB")
    require("readinessProbe" in container, "Prometheus container missing readinessProbe")
    require("livenessProbe" in container, "Prometheus container missing livenessProbe")

    resources = container.get("resources", {})
    require(resources.get("requests", {}).get("cpu") == "100m", "Prometheus CPU request must be 100m")
    require(resources.get("requests", {}).get("memory") == "256Mi", "Prometheus memory request must be 256Mi")
    require(resources.get("limits", {}).get("cpu") == "500m", "Prometheus CPU limit must be 500m")
    require(resources.get("limits", {}).get("memory") == "512Mi", "Prometheus memory limit must be 512Mi")

    storage_volumes = [volume for volume in pod_spec.get("volumes", []) if volume.get("name") == "storage"]
    require(len(storage_volumes) == 1, "Prometheus Deployment must define one storage volume")
    require(storage_volumes[0].get("emptyDir", {}).get("sizeLimit") == "1Gi", "Prometheus emptyDir size limit must be 1Gi")
    ok("Prometheus Deployment manifest is valid")

    require(service.get("kind") == "Service", "prometheus-service.yaml must be kind Service")
    require(service.get("metadata", {}).get("name") == PROMETHEUS_APP, "Prometheus Service name mismatch")
    require(service.get("metadata", {}).get("namespace") == PROMETHEUS_NAMESPACE, "Prometheus Service namespace mismatch")
    require(service.get("spec", {}).get("type") == "ClusterIP", "Prometheus Service must remain ClusterIP-only")
    require(service.get("spec", {}).get("selector", {}).get("app") == PROMETHEUS_APP, "Prometheus Service selector mismatch")
    ports = service.get("spec", {}).get("ports", [])
    require(len(ports) == 1, "Prometheus Service should have one port entry")
    require(ports[0].get("port") == 9090, "Prometheus Service port must be 9090")
    require(ports[0].get("targetPort") == "web", "Prometheus Service targetPort must be web")
    ok("Prometheus ClusterIP Service manifest is valid")


def validate_metrics_server_manifests() -> None:
    require_files(METRICS_SERVER_MANIFEST_DIR, REQUIRED_METRICS_SERVER_FILES)
    ok("All required Metrics Server manifest files exist")

    service_account = load_yaml(METRICS_SERVER_MANIFEST_DIR / "metrics-server-service-account.yaml")
    rbac_documents = load_yaml_documents(METRICS_SERVER_MANIFEST_DIR / "metrics-server-rbac.yaml")
    service = load_yaml(METRICS_SERVER_MANIFEST_DIR / "metrics-server-service.yaml")
    deployment = load_yaml(METRICS_SERVER_MANIFEST_DIR / "metrics-server-deployment.yaml")
    api_service = load_yaml(METRICS_SERVER_MANIFEST_DIR / "metrics-server-api-service.yaml")

    require(service_account.get("kind") == "ServiceAccount", "Metrics Server identity must be a ServiceAccount")
    require(service_account.get("metadata", {}).get("name") == METRICS_SERVER_APP, "Metrics Server ServiceAccount name mismatch")
    require(service_account.get("metadata", {}).get("namespace") == METRICS_SERVER_NAMESPACE, "Metrics Server ServiceAccount namespace mismatch")
    ok("Metrics Server ServiceAccount manifest is valid")

    rbac_resources = {
        (
            document.get("kind"),
            document.get("metadata", {}).get("name"),
            document.get("metadata", {}).get("namespace"),
        ): document
        for document in rbac_documents
    }
    expected_rbac_resources = {
        ("ClusterRole", "system:aggregated-metrics-reader", None),
        ("RoleBinding", "metrics-server-auth-reader", METRICS_SERVER_NAMESPACE),
        ("ClusterRoleBinding", "metrics-server:system:auth-delegator", None),
        ("ClusterRole", "system:metrics-server", None),
        ("ClusterRoleBinding", "system:metrics-server", None),
    }
    require(len(rbac_documents) == 5, "Metrics Server RBAC manifest must contain five resources")
    require(set(rbac_resources) == expected_rbac_resources, "Metrics Server RBAC resource set mismatch")

    for document in rbac_documents:
        for rule in document.get("rules", []):
            require("*" not in rule.get("apiGroups", []), "Metrics Server RBAC must not grant wildcard API groups")
            require("*" not in rule.get("resources", []), "Metrics Server RBAC must not grant wildcard resources")
            require("*" not in rule.get("verbs", []), "Metrics Server RBAC must not grant wildcard verbs")

    aggregated_reader = rbac_resources[("ClusterRole", "system:aggregated-metrics-reader", None)]
    aggregated_rules = aggregated_reader.get("rules", [])
    require(len(aggregated_rules) == 1, "Aggregated metrics reader must contain one rule")
    require(aggregated_rules[0].get("apiGroups") == ["metrics.k8s.io"], "Aggregated metrics reader API group mismatch")
    require(set(aggregated_rules[0].get("resources", [])) == {"nodes", "pods"}, "Aggregated metrics reader resources mismatch")
    require(set(aggregated_rules[0].get("verbs", [])) == {"get", "list", "watch"}, "Aggregated metrics reader verbs mismatch")

    metrics_role = rbac_resources[("ClusterRole", "system:metrics-server", None)]
    metrics_rules = metrics_role.get("rules", [])
    require(len(metrics_rules) == 2, "Metrics Server ClusterRole must contain two rules")
    require(
        any(rule.get("resources") == ["nodes/metrics"] and rule.get("verbs") == ["get"] for rule in metrics_rules),
        "Metrics Server ClusterRole must grant get on nodes/metrics",
    )
    require(
        any(
            set(rule.get("resources", [])) == {"nodes", "pods"}
            and set(rule.get("verbs", [])) == {"get", "list", "watch"}
            for rule in metrics_rules
        ),
        "Metrics Server ClusterRole must grant read-only Node and Pod discovery",
    )
    ok("Metrics Server upstream RBAC manifests are valid")

    require(service.get("kind") == "Service", "Metrics Server Service manifest must be kind Service")
    require(service.get("metadata", {}).get("name") == METRICS_SERVER_APP, "Metrics Server Service name mismatch")
    require(service.get("metadata", {}).get("namespace") == METRICS_SERVER_NAMESPACE, "Metrics Server Service namespace mismatch")
    require(service.get("spec", {}).get("type") == "ClusterIP", "Metrics Server Service must be ClusterIP")
    require(service.get("spec", {}).get("selector", {}).get("k8s-app") == METRICS_SERVER_APP, "Metrics Server Service selector mismatch")
    service_ports = service.get("spec", {}).get("ports", [])
    require(len(service_ports) == 1, "Metrics Server Service should contain one port")
    require(service_ports[0].get("port") == 443, "Metrics Server Service port must be 443")
    require(service_ports[0].get("targetPort") == "https", "Metrics Server Service targetPort must be https")
    ok("Metrics Server ClusterIP Service manifest is valid")

    require(deployment.get("kind") == "Deployment", "Metrics Server workload must be a Deployment")
    require(deployment.get("metadata", {}).get("name") == METRICS_SERVER_APP, "Metrics Server Deployment name mismatch")
    require(deployment.get("metadata", {}).get("namespace") == METRICS_SERVER_NAMESPACE, "Metrics Server Deployment namespace mismatch")
    require(deployment.get("spec", {}).get("replicas") == 1, "Metrics Server must use one replica")

    pod_spec = deployment.get("spec", {}).get("template", {}).get("spec", {})
    require(pod_spec.get("serviceAccountName") == METRICS_SERVER_APP, "Metrics Server Deployment ServiceAccount mismatch")
    require(pod_spec.get("automountServiceAccountToken") is True, "Metrics Server requires its service-account CA and token mount")
    require("hostNetwork" not in pod_spec, "Metrics Server must not use host networking")
    require(
        not any("hostPath" in volume for volume in pod_spec.get("volumes", [])),
        "Metrics Server must not mount host paths",
    )

    containers = pod_spec.get("containers", [])
    require(len(containers) == 1, "Metrics Server Deployment should have exactly one container")
    container = containers[0]
    require(container.get("name") == METRICS_SERVER_APP, "Metrics Server container name mismatch")
    require(container.get("image") == METRICS_SERVER_IMAGE, "Metrics Server image must be pinned to v0.9.0")

    arguments = container.get("args", [])
    require(METRICS_SERVER_CA_ARGUMENT in arguments, "Metrics Server must validate kubelets with the service-account CA")
    require("--kubelet-insecure-tls" not in arguments, "Metrics Server must not disable kubelet TLS verification")
    require(
        "--kubelet-preferred-address-types=InternalIP,ExternalIP,Hostname" in arguments,
        "Metrics Server must prefer node InternalIP addresses",
    )
    require("--metric-resolution=15s" in arguments, "Metrics Server resolution must be 15 seconds")

    resources = container.get("resources", {})
    require(resources.get("requests", {}).get("cpu") == "100m", "Metrics Server CPU request must be 100m")
    require(resources.get("requests", {}).get("memory") == "200Mi", "Metrics Server memory request must be 200Mi")
    require("readinessProbe" in container, "Metrics Server container missing readinessProbe")
    require("livenessProbe" in container, "Metrics Server container missing livenessProbe")

    security_context = container.get("securityContext", {})
    require(security_context.get("allowPrivilegeEscalation") is False, "Metrics Server must forbid privilege escalation")
    require(security_context.get("readOnlyRootFilesystem") is True, "Metrics Server root filesystem must be read-only")
    require(security_context.get("runAsNonRoot") is True, "Metrics Server must run as non-root")
    require(security_context.get("seccompProfile", {}).get("type") == "RuntimeDefault", "Metrics Server must use RuntimeDefault seccomp")
    require(security_context.get("capabilities", {}).get("drop") == ["ALL"], "Metrics Server must drop all Linux capabilities")
    ok("Metrics Server Deployment manifest is valid and forbids insecure kubelet TLS")

    require(api_service.get("kind") == "APIService", "Metrics API registration must be kind APIService")
    require(api_service.get("metadata", {}).get("name") == "v1beta1.metrics.k8s.io", "Metrics APIService name mismatch")
    api_service_spec = api_service.get("spec", {})
    require(api_service_spec.get("group") == "metrics.k8s.io", "Metrics APIService group mismatch")
    require(api_service_spec.get("version") == "v1beta1", "Metrics APIService version mismatch")
    require(api_service_spec.get("service", {}).get("name") == METRICS_SERVER_APP, "Metrics APIService target Service mismatch")
    require(api_service_spec.get("service", {}).get("namespace") == METRICS_SERVER_NAMESPACE, "Metrics APIService target namespace mismatch")
    require(api_service_spec.get("insecureSkipTLSVerify") is True, "Metrics APIService must match the upstream ephemeral-serving-certificate model")
    ok("Metrics APIService manifest is valid")


def main() -> None:
    validate_restaurant_manifests()
    validate_prometheus_manifests()
    validate_metrics_server_manifests()
    print()
    print("All Kubernetes manifest checks passed.")


if __name__ == "__main__":
    main()
